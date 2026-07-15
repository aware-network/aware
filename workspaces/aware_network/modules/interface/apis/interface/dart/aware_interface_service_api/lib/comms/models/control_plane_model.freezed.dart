// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'control_plane_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$InterfaceControlPlaneOperation {

 InterfaceControlPlaneRequest? get request; InterfaceControlPlaneResponse? get response; InterfaceControlPlaneNotification? get notification;
/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceControlPlaneOperationCopyWith<InterfaceControlPlaneOperation> get copyWith => _$InterfaceControlPlaneOperationCopyWithImpl<InterfaceControlPlaneOperation>(this as InterfaceControlPlaneOperation, _$identity);

  /// Serializes this InterfaceControlPlaneOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceControlPlaneOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response)&&(identical(other.notification, notification) || other.notification == notification));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response,notification);

@override
String toString() {
  return 'InterfaceControlPlaneOperation(request: $request, response: $response, notification: $notification)';
}


}

/// @nodoc
abstract mixin class $InterfaceControlPlaneOperationCopyWith<$Res>  {
  factory $InterfaceControlPlaneOperationCopyWith(InterfaceControlPlaneOperation value, $Res Function(InterfaceControlPlaneOperation) _then) = _$InterfaceControlPlaneOperationCopyWithImpl;
@useResult
$Res call({
 InterfaceControlPlaneRequest? request, InterfaceControlPlaneResponse? response, InterfaceControlPlaneNotification? notification
});


$InterfaceControlPlaneRequestCopyWith<$Res>? get request;$InterfaceControlPlaneResponseCopyWith<$Res>? get response;$InterfaceControlPlaneNotificationCopyWith<$Res>? get notification;

}
/// @nodoc
class _$InterfaceControlPlaneOperationCopyWithImpl<$Res>
    implements $InterfaceControlPlaneOperationCopyWith<$Res> {
  _$InterfaceControlPlaneOperationCopyWithImpl(this._self, this._then);

  final InterfaceControlPlaneOperation _self;
  final $Res Function(InterfaceControlPlaneOperation) _then;

/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? request = freezed,Object? response = freezed,Object? notification = freezed,}) {
  return _then(_self.copyWith(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as InterfaceControlPlaneRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as InterfaceControlPlaneResponse?,notification: freezed == notification ? _self.notification : notification // ignore: cast_nullable_to_non_nullable
as InterfaceControlPlaneNotification?,
  ));
}
/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceControlPlaneRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $InterfaceControlPlaneRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceControlPlaneResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $InterfaceControlPlaneResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceControlPlaneNotificationCopyWith<$Res>? get notification {
    if (_self.notification == null) {
    return null;
  }

  return $InterfaceControlPlaneNotificationCopyWith<$Res>(_self.notification!, (value) {
    return _then(_self.copyWith(notification: value));
  });
}
}


/// Adds pattern-matching-related methods to [InterfaceControlPlaneOperation].
extension InterfaceControlPlaneOperationPatterns on InterfaceControlPlaneOperation {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceControlPlaneOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceControlPlaneOperation() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceControlPlaneOperation value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceControlPlaneOperation():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceControlPlaneOperation value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceControlPlaneOperation() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( InterfaceControlPlaneRequest? request,  InterfaceControlPlaneResponse? response,  InterfaceControlPlaneNotification? notification)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceControlPlaneOperation() when def != null:
return def(_that.request,_that.response,_that.notification);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( InterfaceControlPlaneRequest? request,  InterfaceControlPlaneResponse? response,  InterfaceControlPlaneNotification? notification)  def,}) {final _that = this;
switch (_that) {
case _InterfaceControlPlaneOperation():
return def(_that.request,_that.response,_that.notification);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( InterfaceControlPlaneRequest? request,  InterfaceControlPlaneResponse? response,  InterfaceControlPlaneNotification? notification)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceControlPlaneOperation() when def != null:
return def(_that.request,_that.response,_that.notification);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceControlPlaneOperation implements InterfaceControlPlaneOperation {
   _InterfaceControlPlaneOperation({this.request, this.response, this.notification});
  factory _InterfaceControlPlaneOperation.fromJson(Map<String, dynamic> json) => _$InterfaceControlPlaneOperationFromJson(json);

@override final  InterfaceControlPlaneRequest? request;
@override final  InterfaceControlPlaneResponse? response;
@override final  InterfaceControlPlaneNotification? notification;

/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceControlPlaneOperationCopyWith<_InterfaceControlPlaneOperation> get copyWith => __$InterfaceControlPlaneOperationCopyWithImpl<_InterfaceControlPlaneOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceControlPlaneOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceControlPlaneOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response)&&(identical(other.notification, notification) || other.notification == notification));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response,notification);

@override
String toString() {
  return 'InterfaceControlPlaneOperation.def(request: $request, response: $response, notification: $notification)';
}


}

/// @nodoc
abstract mixin class _$InterfaceControlPlaneOperationCopyWith<$Res> implements $InterfaceControlPlaneOperationCopyWith<$Res> {
  factory _$InterfaceControlPlaneOperationCopyWith(_InterfaceControlPlaneOperation value, $Res Function(_InterfaceControlPlaneOperation) _then) = __$InterfaceControlPlaneOperationCopyWithImpl;
@override @useResult
$Res call({
 InterfaceControlPlaneRequest? request, InterfaceControlPlaneResponse? response, InterfaceControlPlaneNotification? notification
});


@override $InterfaceControlPlaneRequestCopyWith<$Res>? get request;@override $InterfaceControlPlaneResponseCopyWith<$Res>? get response;@override $InterfaceControlPlaneNotificationCopyWith<$Res>? get notification;

}
/// @nodoc
class __$InterfaceControlPlaneOperationCopyWithImpl<$Res>
    implements _$InterfaceControlPlaneOperationCopyWith<$Res> {
  __$InterfaceControlPlaneOperationCopyWithImpl(this._self, this._then);

  final _InterfaceControlPlaneOperation _self;
  final $Res Function(_InterfaceControlPlaneOperation) _then;

/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? request = freezed,Object? response = freezed,Object? notification = freezed,}) {
  return _then(_InterfaceControlPlaneOperation(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as InterfaceControlPlaneRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as InterfaceControlPlaneResponse?,notification: freezed == notification ? _self.notification : notification // ignore: cast_nullable_to_non_nullable
as InterfaceControlPlaneNotification?,
  ));
}

/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceControlPlaneRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $InterfaceControlPlaneRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceControlPlaneResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $InterfaceControlPlaneResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}/// Create a copy of InterfaceControlPlaneOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceControlPlaneNotificationCopyWith<$Res>? get notification {
    if (_self.notification == null) {
    return null;
  }

  return $InterfaceControlPlaneNotificationCopyWith<$Res>(_self.notification!, (value) {
    return _then(_self.copyWith(notification: value));
  });
}
}

InterfaceControlPlaneRequest _$InterfaceControlPlaneRequestFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'ping':
          return PingRequest.fromJson(
            json
          );
                case 'namespace_ensure':
          return NamespaceEnsureRequest.fromJson(
            json
          );
                case 'namespace_list':
          return NamespaceListRequest.fromJson(
            json
          );
                case 'interface_status':
          return InterfaceStatusRequest.fromJson(
            json
          );
                case 'interface_admit_environment_actor':
          return InterfaceAdmitEnvironmentActorRequest.fromJson(
            json
          );
                case 'interface_join_environment_session':
          return InterfaceJoinEnvironmentSessionRequest.fromJson(
            json
          );
                case 'interface_select_environment_navigation_target':
          return InterfaceSelectEnvironmentNavigationTargetRequest.fromJson(
            json
          );
                case 'interface_enter_environment':
          return InterfaceEnterEnvironmentRequest.fromJson(
            json
          );
                case 'interface_resolve_experience_lens':
          return InterfaceResolveExperienceLensRequest.fromJson(
            json
          );
                case 'interface_action':
          return InterfaceActionRequest.fromJson(
            json
          );
                case 'interface_select_step':
          return InterfaceSelectStepRequest.fromJson(
            json
          );
                case 'interface_select_profile':
          return InterfaceSelectProfileRequest.fromJson(
            json
          );
                case 'interface_select_runtime_layout':
          return InterfaceSelectRuntimeLayoutRequest.fromJson(
            json
          );
                case 'interface_activate_runtime_focus':
          return InterfaceActivateRuntimeFocusRequest.fromJson(
            json
          );
                case 'interface_request_window_layout':
          return InterfaceRequestWindowLayoutRequest.fromJson(
            json
          );
                case 'interface_apply_attention_layout_transition':
          return InterfaceApplyAttentionLayoutTransitionRequest.fromJson(
            json
          );
                case 'interface_apply_attention_layout_topology_transition':
          return InterfaceApplyAttentionLayoutTopologyTransitionRequest.fromJson(
            json
          );
                case 'interface_report_renderer_capabilities':
          return InterfaceReportRendererCapabilitiesRequest.fromJson(
            json
          );
                case 'interface_sync_view_state_cursor':
          return InterfaceSyncViewStateCursorRequest.fromJson(
            json
          );
                case 'interface_follow':
          return InterfaceFollowRequest.fromJson(
            json
          );
                case 'interface_invoke_api':
          return InterfaceInvokeApiRequest.fromJson(
            json
          );
                case 'interface_stream_api':
          return InterfaceStreamApiRequest.fromJson(
            json
          );
                case 'interface_stop':
          return InterfaceStopRequest.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'InterfaceControlPlaneRequest',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$InterfaceControlPlaneRequest {

@UuidValueConverter() UuidValue? get requestId; int get protocolVersion;
/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceControlPlaneRequestCopyWith<InterfaceControlPlaneRequest> get copyWith => _$InterfaceControlPlaneRequestCopyWithImpl<InterfaceControlPlaneRequest>(this as InterfaceControlPlaneRequest, _$identity);

  /// Serializes this InterfaceControlPlaneRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceControlPlaneRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion);

@override
String toString() {
  return 'InterfaceControlPlaneRequest(requestId: $requestId, protocolVersion: $protocolVersion)';
}


}

/// @nodoc
abstract mixin class $InterfaceControlPlaneRequestCopyWith<$Res>  {
  factory $InterfaceControlPlaneRequestCopyWith(InterfaceControlPlaneRequest value, $Res Function(InterfaceControlPlaneRequest) _then) = _$InterfaceControlPlaneRequestCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion
});




}
/// @nodoc
class _$InterfaceControlPlaneRequestCopyWithImpl<$Res>
    implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  _$InterfaceControlPlaneRequestCopyWithImpl(this._self, this._then);

  final InterfaceControlPlaneRequest _self;
  final $Res Function(InterfaceControlPlaneRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? protocolVersion = null,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceControlPlaneRequest].
extension InterfaceControlPlaneRequestPatterns on InterfaceControlPlaneRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( PingRequest value)?  ping,TResult Function( NamespaceEnsureRequest value)?  namespaceEnsure,TResult Function( NamespaceListRequest value)?  namespaceList,TResult Function( InterfaceStatusRequest value)?  interfaceStatus,TResult Function( InterfaceAdmitEnvironmentActorRequest value)?  interfaceAdmitEnvironmentActor,TResult Function( InterfaceJoinEnvironmentSessionRequest value)?  interfaceJoinEnvironmentSession,TResult Function( InterfaceSelectEnvironmentNavigationTargetRequest value)?  interfaceSelectEnvironmentNavigationTarget,TResult Function( InterfaceEnterEnvironmentRequest value)?  interfaceEnterEnvironment,TResult Function( InterfaceResolveExperienceLensRequest value)?  interfaceResolveExperienceLens,TResult Function( InterfaceActionRequest value)?  interfaceAction,TResult Function( InterfaceSelectStepRequest value)?  interfaceSelectStep,TResult Function( InterfaceSelectProfileRequest value)?  interfaceSelectProfile,TResult Function( InterfaceSelectRuntimeLayoutRequest value)?  interfaceSelectRuntimeLayout,TResult Function( InterfaceActivateRuntimeFocusRequest value)?  interfaceActivateRuntimeFocus,TResult Function( InterfaceRequestWindowLayoutRequest value)?  interfaceRequestWindowLayout,TResult Function( InterfaceApplyAttentionLayoutTransitionRequest value)?  interfaceApplyAttentionLayoutTransition,TResult Function( InterfaceApplyAttentionLayoutTopologyTransitionRequest value)?  interfaceApplyAttentionLayoutTopologyTransition,TResult Function( InterfaceReportRendererCapabilitiesRequest value)?  interfaceReportRendererCapabilities,TResult Function( InterfaceSyncViewStateCursorRequest value)?  interfaceSyncViewStateCursor,TResult Function( InterfaceFollowRequest value)?  interfaceFollow,TResult Function( InterfaceInvokeApiRequest value)?  interfaceInvokeApi,TResult Function( InterfaceStreamApiRequest value)?  interfaceStreamApi,TResult Function( InterfaceStopRequest value)?  interfaceStop,required TResult orElse(),}){
final _that = this;
switch (_that) {
case PingRequest() when ping != null:
return ping(_that);case NamespaceEnsureRequest() when namespaceEnsure != null:
return namespaceEnsure(_that);case NamespaceListRequest() when namespaceList != null:
return namespaceList(_that);case InterfaceStatusRequest() when interfaceStatus != null:
return interfaceStatus(_that);case InterfaceAdmitEnvironmentActorRequest() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that);case InterfaceJoinEnvironmentSessionRequest() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that);case InterfaceSelectEnvironmentNavigationTargetRequest() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that);case InterfaceEnterEnvironmentRequest() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that);case InterfaceResolveExperienceLensRequest() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that);case InterfaceActionRequest() when interfaceAction != null:
return interfaceAction(_that);case InterfaceSelectStepRequest() when interfaceSelectStep != null:
return interfaceSelectStep(_that);case InterfaceSelectProfileRequest() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that);case InterfaceSelectRuntimeLayoutRequest() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that);case InterfaceActivateRuntimeFocusRequest() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that);case InterfaceRequestWindowLayoutRequest() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that);case InterfaceApplyAttentionLayoutTransitionRequest() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that);case InterfaceApplyAttentionLayoutTopologyTransitionRequest() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that);case InterfaceReportRendererCapabilitiesRequest() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that);case InterfaceSyncViewStateCursorRequest() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that);case InterfaceFollowRequest() when interfaceFollow != null:
return interfaceFollow(_that);case InterfaceInvokeApiRequest() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that);case InterfaceStreamApiRequest() when interfaceStreamApi != null:
return interfaceStreamApi(_that);case InterfaceStopRequest() when interfaceStop != null:
return interfaceStop(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( PingRequest value)  ping,required TResult Function( NamespaceEnsureRequest value)  namespaceEnsure,required TResult Function( NamespaceListRequest value)  namespaceList,required TResult Function( InterfaceStatusRequest value)  interfaceStatus,required TResult Function( InterfaceAdmitEnvironmentActorRequest value)  interfaceAdmitEnvironmentActor,required TResult Function( InterfaceJoinEnvironmentSessionRequest value)  interfaceJoinEnvironmentSession,required TResult Function( InterfaceSelectEnvironmentNavigationTargetRequest value)  interfaceSelectEnvironmentNavigationTarget,required TResult Function( InterfaceEnterEnvironmentRequest value)  interfaceEnterEnvironment,required TResult Function( InterfaceResolveExperienceLensRequest value)  interfaceResolveExperienceLens,required TResult Function( InterfaceActionRequest value)  interfaceAction,required TResult Function( InterfaceSelectStepRequest value)  interfaceSelectStep,required TResult Function( InterfaceSelectProfileRequest value)  interfaceSelectProfile,required TResult Function( InterfaceSelectRuntimeLayoutRequest value)  interfaceSelectRuntimeLayout,required TResult Function( InterfaceActivateRuntimeFocusRequest value)  interfaceActivateRuntimeFocus,required TResult Function( InterfaceRequestWindowLayoutRequest value)  interfaceRequestWindowLayout,required TResult Function( InterfaceApplyAttentionLayoutTransitionRequest value)  interfaceApplyAttentionLayoutTransition,required TResult Function( InterfaceApplyAttentionLayoutTopologyTransitionRequest value)  interfaceApplyAttentionLayoutTopologyTransition,required TResult Function( InterfaceReportRendererCapabilitiesRequest value)  interfaceReportRendererCapabilities,required TResult Function( InterfaceSyncViewStateCursorRequest value)  interfaceSyncViewStateCursor,required TResult Function( InterfaceFollowRequest value)  interfaceFollow,required TResult Function( InterfaceInvokeApiRequest value)  interfaceInvokeApi,required TResult Function( InterfaceStreamApiRequest value)  interfaceStreamApi,required TResult Function( InterfaceStopRequest value)  interfaceStop,}){
final _that = this;
switch (_that) {
case PingRequest():
return ping(_that);case NamespaceEnsureRequest():
return namespaceEnsure(_that);case NamespaceListRequest():
return namespaceList(_that);case InterfaceStatusRequest():
return interfaceStatus(_that);case InterfaceAdmitEnvironmentActorRequest():
return interfaceAdmitEnvironmentActor(_that);case InterfaceJoinEnvironmentSessionRequest():
return interfaceJoinEnvironmentSession(_that);case InterfaceSelectEnvironmentNavigationTargetRequest():
return interfaceSelectEnvironmentNavigationTarget(_that);case InterfaceEnterEnvironmentRequest():
return interfaceEnterEnvironment(_that);case InterfaceResolveExperienceLensRequest():
return interfaceResolveExperienceLens(_that);case InterfaceActionRequest():
return interfaceAction(_that);case InterfaceSelectStepRequest():
return interfaceSelectStep(_that);case InterfaceSelectProfileRequest():
return interfaceSelectProfile(_that);case InterfaceSelectRuntimeLayoutRequest():
return interfaceSelectRuntimeLayout(_that);case InterfaceActivateRuntimeFocusRequest():
return interfaceActivateRuntimeFocus(_that);case InterfaceRequestWindowLayoutRequest():
return interfaceRequestWindowLayout(_that);case InterfaceApplyAttentionLayoutTransitionRequest():
return interfaceApplyAttentionLayoutTransition(_that);case InterfaceApplyAttentionLayoutTopologyTransitionRequest():
return interfaceApplyAttentionLayoutTopologyTransition(_that);case InterfaceReportRendererCapabilitiesRequest():
return interfaceReportRendererCapabilities(_that);case InterfaceSyncViewStateCursorRequest():
return interfaceSyncViewStateCursor(_that);case InterfaceFollowRequest():
return interfaceFollow(_that);case InterfaceInvokeApiRequest():
return interfaceInvokeApi(_that);case InterfaceStreamApiRequest():
return interfaceStreamApi(_that);case InterfaceStopRequest():
return interfaceStop(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( PingRequest value)?  ping,TResult? Function( NamespaceEnsureRequest value)?  namespaceEnsure,TResult? Function( NamespaceListRequest value)?  namespaceList,TResult? Function( InterfaceStatusRequest value)?  interfaceStatus,TResult? Function( InterfaceAdmitEnvironmentActorRequest value)?  interfaceAdmitEnvironmentActor,TResult? Function( InterfaceJoinEnvironmentSessionRequest value)?  interfaceJoinEnvironmentSession,TResult? Function( InterfaceSelectEnvironmentNavigationTargetRequest value)?  interfaceSelectEnvironmentNavigationTarget,TResult? Function( InterfaceEnterEnvironmentRequest value)?  interfaceEnterEnvironment,TResult? Function( InterfaceResolveExperienceLensRequest value)?  interfaceResolveExperienceLens,TResult? Function( InterfaceActionRequest value)?  interfaceAction,TResult? Function( InterfaceSelectStepRequest value)?  interfaceSelectStep,TResult? Function( InterfaceSelectProfileRequest value)?  interfaceSelectProfile,TResult? Function( InterfaceSelectRuntimeLayoutRequest value)?  interfaceSelectRuntimeLayout,TResult? Function( InterfaceActivateRuntimeFocusRequest value)?  interfaceActivateRuntimeFocus,TResult? Function( InterfaceRequestWindowLayoutRequest value)?  interfaceRequestWindowLayout,TResult? Function( InterfaceApplyAttentionLayoutTransitionRequest value)?  interfaceApplyAttentionLayoutTransition,TResult? Function( InterfaceApplyAttentionLayoutTopologyTransitionRequest value)?  interfaceApplyAttentionLayoutTopologyTransition,TResult? Function( InterfaceReportRendererCapabilitiesRequest value)?  interfaceReportRendererCapabilities,TResult? Function( InterfaceSyncViewStateCursorRequest value)?  interfaceSyncViewStateCursor,TResult? Function( InterfaceFollowRequest value)?  interfaceFollow,TResult? Function( InterfaceInvokeApiRequest value)?  interfaceInvokeApi,TResult? Function( InterfaceStreamApiRequest value)?  interfaceStreamApi,TResult? Function( InterfaceStopRequest value)?  interfaceStop,}){
final _that = this;
switch (_that) {
case PingRequest() when ping != null:
return ping(_that);case NamespaceEnsureRequest() when namespaceEnsure != null:
return namespaceEnsure(_that);case NamespaceListRequest() when namespaceList != null:
return namespaceList(_that);case InterfaceStatusRequest() when interfaceStatus != null:
return interfaceStatus(_that);case InterfaceAdmitEnvironmentActorRequest() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that);case InterfaceJoinEnvironmentSessionRequest() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that);case InterfaceSelectEnvironmentNavigationTargetRequest() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that);case InterfaceEnterEnvironmentRequest() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that);case InterfaceResolveExperienceLensRequest() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that);case InterfaceActionRequest() when interfaceAction != null:
return interfaceAction(_that);case InterfaceSelectStepRequest() when interfaceSelectStep != null:
return interfaceSelectStep(_that);case InterfaceSelectProfileRequest() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that);case InterfaceSelectRuntimeLayoutRequest() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that);case InterfaceActivateRuntimeFocusRequest() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that);case InterfaceRequestWindowLayoutRequest() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that);case InterfaceApplyAttentionLayoutTransitionRequest() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that);case InterfaceApplyAttentionLayoutTopologyTransitionRequest() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that);case InterfaceReportRendererCapabilitiesRequest() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that);case InterfaceSyncViewStateCursorRequest() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that);case InterfaceFollowRequest() when interfaceFollow != null:
return interfaceFollow(_that);case InterfaceInvokeApiRequest() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that);case InterfaceStreamApiRequest() when interfaceStreamApi != null:
return interfaceStreamApi(_that);case InterfaceStopRequest() when interfaceStop != null:
return interfaceStop(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion)?  ping,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? hostLabel,  String? endpoint,  String? authToken, @UuidValueConverter()  UuidValue? environmentConfigId, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName)?  namespaceEnsure,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion)?  namespaceList,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace)?  interfaceStatus,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue actorConfigId, @UuidValueConverter()  UuidValue classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  String? reason,  Map<String, dynamic> evidence)?  interfaceAdmitEnvironmentActor,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentProfileId,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  String? reason,  Map<String, dynamic> evidence)?  interfaceJoinEnvironmentSession,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentNavigationContextId, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId,  String? reason,  Map<String, dynamic> evidence)?  interfaceSelectEnvironmentNavigationTarget,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentProfileId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt, @UuidValueConverter()  UuidValue? environmentSessionId, @UuidValueConverter()  UuidValue? environmentSessionConfigId,  String? sessionKey,  String? title,  String? description,  String? purpose,  String? sourceKind,  String? sourceRef,  String? reason,  Map<String, dynamic> evidence)?  interfaceEnterEnvironment,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  ExperienceActorConfigAdmissionReceipt? experienceActorAdmission, @UuidValueConverter()  UuidValue? experienceIdentitySessionConfigId,  String? reason,  Map<String, dynamic> evidence)?  interfaceResolveExperienceLens,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? paneRef,  String actionKey,  String? actionKind,  String? operationRef,  String? sdkOperationId,  String? paneConfigSdkOperationId,  String? endpointRef,  String? apiCapabilityEndpointId,  String? paneConfigApiCapabilityEndpointId,  Map<String, dynamic> payload)?  interfaceAction,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? stepId)?  interfaceSelectStep,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String profileId)?  interfaceSelectProfile,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? layoutConfigId)?  interfaceSelectRuntimeLayout,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? representationId)?  interfaceActivateRuntimeFocus,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName,  String? windowKey, @UuidValueConverter()  UuidValue? layoutConfigId,  String? layoutKey,  String? sectionKey, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? representationId,  String? requestedByService,  String? requestedByOperation,  String? reason,  String? idempotencyKey)?  interfaceRequestWindowLayout,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String clientIntentId, @UuidValueConverter()  UuidValue? expectedPreviousLayoutTransitionId, @UuidValueConverter()  UuidValue? topologyTransitionId,  List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates)?  interfaceApplyAttentionLayoutTransition,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String clientIntentId, @UuidValueConverter()  UuidValue? expectedPreviousTopologyTransitionId,  List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates)?  interfaceApplyAttentionLayoutTopologyTransition,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  InterfaceRendererCapabilitiesState rendererCapabilities)?  interfaceReportRendererCapabilities,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? rendererId,  String? knownCursor,  String? knownDigest)?  interfaceSyncViewStateCursor,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  int pollIntervalMs)?  interfaceFollow,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  Map<String, dynamic> requestPayload)?  interfaceInvokeApi,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  Map<String, dynamic> requestPayload)?  interfaceStreamApi,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace)?  interfaceStop,required TResult orElse(),}) {final _that = this;
switch (_that) {
case PingRequest() when ping != null:
return ping(_that.requestId,_that.protocolVersion);case NamespaceEnsureRequest() when namespaceEnsure != null:
return namespaceEnsure(_that.requestId,_that.protocolVersion,_that.namespace,_that.hostLabel,_that.endpoint,_that.authToken,_that.environmentConfigId,_that.interfacePackageId,_that.interfacePackageName);case NamespaceListRequest() when namespaceList != null:
return namespaceList(_that.requestId,_that.protocolVersion);case InterfaceStatusRequest() when interfaceStatus != null:
return interfaceStatus(_that.requestId,_that.protocolVersion,_that.namespace);case InterfaceAdmitEnvironmentActorRequest() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentId,_that.environmentProfileId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.reason,_that.evidence);case InterfaceJoinEnvironmentSessionRequest() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentSessionId,_that.environmentProfileId,_that.environmentAdmissionReceipt,_that.reason,_that.evidence);case InterfaceSelectEnvironmentNavigationTargetRequest() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentNavigationContextId,_that.selectedProcessId,_that.selectedThreadId,_that.reason,_that.evidence);case InterfaceEnterEnvironmentRequest() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentId,_that.environmentProfileId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.environmentAdmissionReceipt,_that.environmentSessionId,_that.environmentSessionConfigId,_that.sessionKey,_that.title,_that.description,_that.purpose,_that.sourceKind,_that.sourceRef,_that.reason,_that.evidence);case InterfaceResolveExperienceLensRequest() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.experienceActorAdmission,_that.experienceIdentitySessionConfigId,_that.reason,_that.evidence);case InterfaceActionRequest() when interfaceAction != null:
return interfaceAction(_that.requestId,_that.protocolVersion,_that.namespace,_that.paneRef,_that.actionKey,_that.actionKind,_that.operationRef,_that.sdkOperationId,_that.paneConfigSdkOperationId,_that.endpointRef,_that.apiCapabilityEndpointId,_that.paneConfigApiCapabilityEndpointId,_that.payload);case InterfaceSelectStepRequest() when interfaceSelectStep != null:
return interfaceSelectStep(_that.requestId,_that.protocolVersion,_that.namespace,_that.stepId);case InterfaceSelectProfileRequest() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that.requestId,_that.protocolVersion,_that.namespace,_that.profileId);case InterfaceSelectRuntimeLayoutRequest() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that.requestId,_that.protocolVersion,_that.namespace,_that.layoutConfigId);case InterfaceActivateRuntimeFocusRequest() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that.requestId,_that.protocolVersion,_that.namespace,_that.representationId);case InterfaceRequestWindowLayoutRequest() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that.requestId,_that.protocolVersion,_that.namespace,_that.interfacePackageId,_that.interfacePackageName,_that.windowKey,_that.layoutConfigId,_that.layoutKey,_that.sectionKey,_that.observableId,_that.representationId,_that.requestedByService,_that.requestedByOperation,_that.reason,_that.idempotencyKey);case InterfaceApplyAttentionLayoutTransitionRequest() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that.requestId,_that.protocolVersion,_that.namespace,_that.clientIntentId,_that.expectedPreviousLayoutTransitionId,_that.topologyTransitionId,_that.sectionStates);case InterfaceApplyAttentionLayoutTopologyTransitionRequest() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that.requestId,_that.protocolVersion,_that.namespace,_that.clientIntentId,_that.expectedPreviousTopologyTransitionId,_that.sectionStates);case InterfaceReportRendererCapabilitiesRequest() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that.requestId,_that.protocolVersion,_that.namespace,_that.rendererCapabilities);case InterfaceSyncViewStateCursorRequest() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that.requestId,_that.protocolVersion,_that.namespace,_that.rendererId,_that.knownCursor,_that.knownDigest);case InterfaceFollowRequest() when interfaceFollow != null:
return interfaceFollow(_that.requestId,_that.protocolVersion,_that.namespace,_that.pollIntervalMs);case InterfaceInvokeApiRequest() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that.requestId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.requestPayload);case InterfaceStreamApiRequest() when interfaceStreamApi != null:
return interfaceStreamApi(_that.requestId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.requestPayload);case InterfaceStopRequest() when interfaceStop != null:
return interfaceStop(_that.requestId,_that.protocolVersion,_that.namespace);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion)  ping,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? hostLabel,  String? endpoint,  String? authToken, @UuidValueConverter()  UuidValue? environmentConfigId, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName)  namespaceEnsure,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion)  namespaceList,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace)  interfaceStatus,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue actorConfigId, @UuidValueConverter()  UuidValue classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  String? reason,  Map<String, dynamic> evidence)  interfaceAdmitEnvironmentActor,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentProfileId,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  String? reason,  Map<String, dynamic> evidence)  interfaceJoinEnvironmentSession,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentNavigationContextId, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId,  String? reason,  Map<String, dynamic> evidence)  interfaceSelectEnvironmentNavigationTarget,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentProfileId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt, @UuidValueConverter()  UuidValue? environmentSessionId, @UuidValueConverter()  UuidValue? environmentSessionConfigId,  String? sessionKey,  String? title,  String? description,  String? purpose,  String? sourceKind,  String? sourceRef,  String? reason,  Map<String, dynamic> evidence)  interfaceEnterEnvironment,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  ExperienceActorConfigAdmissionReceipt? experienceActorAdmission, @UuidValueConverter()  UuidValue? experienceIdentitySessionConfigId,  String? reason,  Map<String, dynamic> evidence)  interfaceResolveExperienceLens,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? paneRef,  String actionKey,  String? actionKind,  String? operationRef,  String? sdkOperationId,  String? paneConfigSdkOperationId,  String? endpointRef,  String? apiCapabilityEndpointId,  String? paneConfigApiCapabilityEndpointId,  Map<String, dynamic> payload)  interfaceAction,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? stepId)  interfaceSelectStep,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String profileId)  interfaceSelectProfile,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? layoutConfigId)  interfaceSelectRuntimeLayout,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? representationId)  interfaceActivateRuntimeFocus,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName,  String? windowKey, @UuidValueConverter()  UuidValue? layoutConfigId,  String? layoutKey,  String? sectionKey, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? representationId,  String? requestedByService,  String? requestedByOperation,  String? reason,  String? idempotencyKey)  interfaceRequestWindowLayout,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String clientIntentId, @UuidValueConverter()  UuidValue? expectedPreviousLayoutTransitionId, @UuidValueConverter()  UuidValue? topologyTransitionId,  List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates)  interfaceApplyAttentionLayoutTransition,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String clientIntentId, @UuidValueConverter()  UuidValue? expectedPreviousTopologyTransitionId,  List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates)  interfaceApplyAttentionLayoutTopologyTransition,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  InterfaceRendererCapabilitiesState rendererCapabilities)  interfaceReportRendererCapabilities,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? rendererId,  String? knownCursor,  String? knownDigest)  interfaceSyncViewStateCursor,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  int pollIntervalMs)  interfaceFollow,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  Map<String, dynamic> requestPayload)  interfaceInvokeApi,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  Map<String, dynamic> requestPayload)  interfaceStreamApi,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace)  interfaceStop,}) {final _that = this;
switch (_that) {
case PingRequest():
return ping(_that.requestId,_that.protocolVersion);case NamespaceEnsureRequest():
return namespaceEnsure(_that.requestId,_that.protocolVersion,_that.namespace,_that.hostLabel,_that.endpoint,_that.authToken,_that.environmentConfigId,_that.interfacePackageId,_that.interfacePackageName);case NamespaceListRequest():
return namespaceList(_that.requestId,_that.protocolVersion);case InterfaceStatusRequest():
return interfaceStatus(_that.requestId,_that.protocolVersion,_that.namespace);case InterfaceAdmitEnvironmentActorRequest():
return interfaceAdmitEnvironmentActor(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentId,_that.environmentProfileId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.reason,_that.evidence);case InterfaceJoinEnvironmentSessionRequest():
return interfaceJoinEnvironmentSession(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentSessionId,_that.environmentProfileId,_that.environmentAdmissionReceipt,_that.reason,_that.evidence);case InterfaceSelectEnvironmentNavigationTargetRequest():
return interfaceSelectEnvironmentNavigationTarget(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentNavigationContextId,_that.selectedProcessId,_that.selectedThreadId,_that.reason,_that.evidence);case InterfaceEnterEnvironmentRequest():
return interfaceEnterEnvironment(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentId,_that.environmentProfileId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.environmentAdmissionReceipt,_that.environmentSessionId,_that.environmentSessionConfigId,_that.sessionKey,_that.title,_that.description,_that.purpose,_that.sourceKind,_that.sourceRef,_that.reason,_that.evidence);case InterfaceResolveExperienceLensRequest():
return interfaceResolveExperienceLens(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.experienceActorAdmission,_that.experienceIdentitySessionConfigId,_that.reason,_that.evidence);case InterfaceActionRequest():
return interfaceAction(_that.requestId,_that.protocolVersion,_that.namespace,_that.paneRef,_that.actionKey,_that.actionKind,_that.operationRef,_that.sdkOperationId,_that.paneConfigSdkOperationId,_that.endpointRef,_that.apiCapabilityEndpointId,_that.paneConfigApiCapabilityEndpointId,_that.payload);case InterfaceSelectStepRequest():
return interfaceSelectStep(_that.requestId,_that.protocolVersion,_that.namespace,_that.stepId);case InterfaceSelectProfileRequest():
return interfaceSelectProfile(_that.requestId,_that.protocolVersion,_that.namespace,_that.profileId);case InterfaceSelectRuntimeLayoutRequest():
return interfaceSelectRuntimeLayout(_that.requestId,_that.protocolVersion,_that.namespace,_that.layoutConfigId);case InterfaceActivateRuntimeFocusRequest():
return interfaceActivateRuntimeFocus(_that.requestId,_that.protocolVersion,_that.namespace,_that.representationId);case InterfaceRequestWindowLayoutRequest():
return interfaceRequestWindowLayout(_that.requestId,_that.protocolVersion,_that.namespace,_that.interfacePackageId,_that.interfacePackageName,_that.windowKey,_that.layoutConfigId,_that.layoutKey,_that.sectionKey,_that.observableId,_that.representationId,_that.requestedByService,_that.requestedByOperation,_that.reason,_that.idempotencyKey);case InterfaceApplyAttentionLayoutTransitionRequest():
return interfaceApplyAttentionLayoutTransition(_that.requestId,_that.protocolVersion,_that.namespace,_that.clientIntentId,_that.expectedPreviousLayoutTransitionId,_that.topologyTransitionId,_that.sectionStates);case InterfaceApplyAttentionLayoutTopologyTransitionRequest():
return interfaceApplyAttentionLayoutTopologyTransition(_that.requestId,_that.protocolVersion,_that.namespace,_that.clientIntentId,_that.expectedPreviousTopologyTransitionId,_that.sectionStates);case InterfaceReportRendererCapabilitiesRequest():
return interfaceReportRendererCapabilities(_that.requestId,_that.protocolVersion,_that.namespace,_that.rendererCapabilities);case InterfaceSyncViewStateCursorRequest():
return interfaceSyncViewStateCursor(_that.requestId,_that.protocolVersion,_that.namespace,_that.rendererId,_that.knownCursor,_that.knownDigest);case InterfaceFollowRequest():
return interfaceFollow(_that.requestId,_that.protocolVersion,_that.namespace,_that.pollIntervalMs);case InterfaceInvokeApiRequest():
return interfaceInvokeApi(_that.requestId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.requestPayload);case InterfaceStreamApiRequest():
return interfaceStreamApi(_that.requestId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.requestPayload);case InterfaceStopRequest():
return interfaceStop(_that.requestId,_that.protocolVersion,_that.namespace);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion)?  ping,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? hostLabel,  String? endpoint,  String? authToken, @UuidValueConverter()  UuidValue? environmentConfigId, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName)?  namespaceEnsure,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion)?  namespaceList,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace)?  interfaceStatus,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue environmentProfileId, @UuidValueConverter()  UuidValue actorConfigId, @UuidValueConverter()  UuidValue classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  String? reason,  Map<String, dynamic> evidence)?  interfaceAdmitEnvironmentActor,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue environmentSessionId, @UuidValueConverter()  UuidValue? environmentProfileId,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  String? reason,  Map<String, dynamic> evidence)?  interfaceJoinEnvironmentSession,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentNavigationContextId, @UuidValueConverter()  UuidValue? selectedProcessId, @UuidValueConverter()  UuidValue? selectedThreadId,  String? reason,  Map<String, dynamic> evidence)?  interfaceSelectEnvironmentNavigationTarget,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? environmentId, @UuidValueConverter()  UuidValue? environmentProfileId, @UuidValueConverter()  UuidValue? actorConfigId, @UuidValueConverter()  UuidValue? classInstanceIdentityId,  String objectInstanceGraphBranchKey, @UuidValueConverter()  UuidValue? objectInstanceGraphBranchId, @UuidValueListConverter()  List<UuidValue> requestedRoleConfigIds,  List<String> requestedRoleConfigNames,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt, @UuidValueConverter()  UuidValue? environmentSessionId, @UuidValueConverter()  UuidValue? environmentSessionConfigId,  String? sessionKey,  String? title,  String? description,  String? purpose,  String? sourceKind,  String? sourceRef,  String? reason,  Map<String, dynamic> evidence)?  interfaceEnterEnvironment,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  ExperienceActorConfigAdmissionReceipt? experienceActorAdmission, @UuidValueConverter()  UuidValue? experienceIdentitySessionConfigId,  String? reason,  Map<String, dynamic> evidence)?  interfaceResolveExperienceLens,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? paneRef,  String actionKey,  String? actionKind,  String? operationRef,  String? sdkOperationId,  String? paneConfigSdkOperationId,  String? endpointRef,  String? apiCapabilityEndpointId,  String? paneConfigApiCapabilityEndpointId,  Map<String, dynamic> payload)?  interfaceAction,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? stepId)?  interfaceSelectStep,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String profileId)?  interfaceSelectProfile,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? layoutConfigId)?  interfaceSelectRuntimeLayout,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? representationId)?  interfaceActivateRuntimeFocus,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName,  String? windowKey, @UuidValueConverter()  UuidValue? layoutConfigId,  String? layoutKey,  String? sectionKey, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? representationId,  String? requestedByService,  String? requestedByOperation,  String? reason,  String? idempotencyKey)?  interfaceRequestWindowLayout,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String clientIntentId, @UuidValueConverter()  UuidValue? expectedPreviousLayoutTransitionId, @UuidValueConverter()  UuidValue? topologyTransitionId,  List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates)?  interfaceApplyAttentionLayoutTransition,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String clientIntentId, @UuidValueConverter()  UuidValue? expectedPreviousTopologyTransitionId,  List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates)?  interfaceApplyAttentionLayoutTopologyTransition,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  InterfaceRendererCapabilitiesState rendererCapabilities)?  interfaceReportRendererCapabilities,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String? rendererId,  String? knownCursor,  String? knownDigest)?  interfaceSyncViewStateCursor,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  int pollIntervalMs)?  interfaceFollow,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  Map<String, dynamic> requestPayload)?  interfaceInvokeApi,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  Map<String, dynamic> requestPayload)?  interfaceStreamApi,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace)?  interfaceStop,}) {final _that = this;
switch (_that) {
case PingRequest() when ping != null:
return ping(_that.requestId,_that.protocolVersion);case NamespaceEnsureRequest() when namespaceEnsure != null:
return namespaceEnsure(_that.requestId,_that.protocolVersion,_that.namespace,_that.hostLabel,_that.endpoint,_that.authToken,_that.environmentConfigId,_that.interfacePackageId,_that.interfacePackageName);case NamespaceListRequest() when namespaceList != null:
return namespaceList(_that.requestId,_that.protocolVersion);case InterfaceStatusRequest() when interfaceStatus != null:
return interfaceStatus(_that.requestId,_that.protocolVersion,_that.namespace);case InterfaceAdmitEnvironmentActorRequest() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentId,_that.environmentProfileId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.reason,_that.evidence);case InterfaceJoinEnvironmentSessionRequest() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentSessionId,_that.environmentProfileId,_that.environmentAdmissionReceipt,_that.reason,_that.evidence);case InterfaceSelectEnvironmentNavigationTargetRequest() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentNavigationContextId,_that.selectedProcessId,_that.selectedThreadId,_that.reason,_that.evidence);case InterfaceEnterEnvironmentRequest() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentId,_that.environmentProfileId,_that.actorConfigId,_that.classInstanceIdentityId,_that.objectInstanceGraphBranchKey,_that.objectInstanceGraphBranchId,_that.requestedRoleConfigIds,_that.requestedRoleConfigNames,_that.environmentAdmissionReceipt,_that.environmentSessionId,_that.environmentSessionConfigId,_that.sessionKey,_that.title,_that.description,_that.purpose,_that.sourceKind,_that.sourceRef,_that.reason,_that.evidence);case InterfaceResolveExperienceLensRequest() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that.requestId,_that.protocolVersion,_that.namespace,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.experienceActorAdmission,_that.experienceIdentitySessionConfigId,_that.reason,_that.evidence);case InterfaceActionRequest() when interfaceAction != null:
return interfaceAction(_that.requestId,_that.protocolVersion,_that.namespace,_that.paneRef,_that.actionKey,_that.actionKind,_that.operationRef,_that.sdkOperationId,_that.paneConfigSdkOperationId,_that.endpointRef,_that.apiCapabilityEndpointId,_that.paneConfigApiCapabilityEndpointId,_that.payload);case InterfaceSelectStepRequest() when interfaceSelectStep != null:
return interfaceSelectStep(_that.requestId,_that.protocolVersion,_that.namespace,_that.stepId);case InterfaceSelectProfileRequest() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that.requestId,_that.protocolVersion,_that.namespace,_that.profileId);case InterfaceSelectRuntimeLayoutRequest() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that.requestId,_that.protocolVersion,_that.namespace,_that.layoutConfigId);case InterfaceActivateRuntimeFocusRequest() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that.requestId,_that.protocolVersion,_that.namespace,_that.representationId);case InterfaceRequestWindowLayoutRequest() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that.requestId,_that.protocolVersion,_that.namespace,_that.interfacePackageId,_that.interfacePackageName,_that.windowKey,_that.layoutConfigId,_that.layoutKey,_that.sectionKey,_that.observableId,_that.representationId,_that.requestedByService,_that.requestedByOperation,_that.reason,_that.idempotencyKey);case InterfaceApplyAttentionLayoutTransitionRequest() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that.requestId,_that.protocolVersion,_that.namespace,_that.clientIntentId,_that.expectedPreviousLayoutTransitionId,_that.topologyTransitionId,_that.sectionStates);case InterfaceApplyAttentionLayoutTopologyTransitionRequest() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that.requestId,_that.protocolVersion,_that.namespace,_that.clientIntentId,_that.expectedPreviousTopologyTransitionId,_that.sectionStates);case InterfaceReportRendererCapabilitiesRequest() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that.requestId,_that.protocolVersion,_that.namespace,_that.rendererCapabilities);case InterfaceSyncViewStateCursorRequest() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that.requestId,_that.protocolVersion,_that.namespace,_that.rendererId,_that.knownCursor,_that.knownDigest);case InterfaceFollowRequest() when interfaceFollow != null:
return interfaceFollow(_that.requestId,_that.protocolVersion,_that.namespace,_that.pollIntervalMs);case InterfaceInvokeApiRequest() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that.requestId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.requestPayload);case InterfaceStreamApiRequest() when interfaceStreamApi != null:
return interfaceStreamApi(_that.requestId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.requestPayload);case InterfaceStopRequest() when interfaceStop != null:
return interfaceStop(_that.requestId,_that.protocolVersion,_that.namespace);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class PingRequest implements InterfaceControlPlaneRequest {
   PingRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, final  String? $type}): $type = $type ?? 'ping';
  factory PingRequest.fromJson(Map<String, dynamic> json) => _$PingRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PingRequestCopyWith<PingRequest> get copyWith => _$PingRequestCopyWithImpl<PingRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$PingRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PingRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.ping(requestId: $requestId, protocolVersion: $protocolVersion)';
}


}

/// @nodoc
abstract mixin class $PingRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $PingRequestCopyWith(PingRequest value, $Res Function(PingRequest) _then) = _$PingRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion
});




}
/// @nodoc
class _$PingRequestCopyWithImpl<$Res>
    implements $PingRequestCopyWith<$Res> {
  _$PingRequestCopyWithImpl(this._self, this._then);

  final PingRequest _self;
  final $Res Function(PingRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,}) {
  return _then(PingRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class NamespaceEnsureRequest implements InterfaceControlPlaneRequest {
   NamespaceEnsureRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, this.hostLabel, this.endpoint, this.authToken, @UuidValueConverter() this.environmentConfigId, @UuidValueConverter() this.interfacePackageId, this.interfacePackageName, final  String? $type}): $type = $type ?? 'namespace_ensure';
  factory NamespaceEnsureRequest.fromJson(Map<String, dynamic> json) => _$NamespaceEnsureRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String? hostLabel;
 final  String? endpoint;
 final  String? authToken;
@UuidValueConverter() final  UuidValue? environmentConfigId;
@UuidValueConverter() final  UuidValue? interfacePackageId;
 final  String? interfacePackageName;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NamespaceEnsureRequestCopyWith<NamespaceEnsureRequest> get copyWith => _$NamespaceEnsureRequestCopyWithImpl<NamespaceEnsureRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NamespaceEnsureRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NamespaceEnsureRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostLabel, hostLabel) || other.hostLabel == hostLabel)&&(identical(other.endpoint, endpoint) || other.endpoint == endpoint)&&(identical(other.authToken, authToken) || other.authToken == authToken)&&(identical(other.environmentConfigId, environmentConfigId) || other.environmentConfigId == environmentConfigId)&&(identical(other.interfacePackageId, interfacePackageId) || other.interfacePackageId == interfacePackageId)&&(identical(other.interfacePackageName, interfacePackageName) || other.interfacePackageName == interfacePackageName));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,hostLabel,endpoint,authToken,environmentConfigId,interfacePackageId,interfacePackageName);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.namespaceEnsure(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, hostLabel: $hostLabel, endpoint: $endpoint, authToken: $authToken, environmentConfigId: $environmentConfigId, interfacePackageId: $interfacePackageId, interfacePackageName: $interfacePackageName)';
}


}

/// @nodoc
abstract mixin class $NamespaceEnsureRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $NamespaceEnsureRequestCopyWith(NamespaceEnsureRequest value, $Res Function(NamespaceEnsureRequest) _then) = _$NamespaceEnsureRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String? hostLabel, String? endpoint, String? authToken,@UuidValueConverter() UuidValue? environmentConfigId,@UuidValueConverter() UuidValue? interfacePackageId, String? interfacePackageName
});




}
/// @nodoc
class _$NamespaceEnsureRequestCopyWithImpl<$Res>
    implements $NamespaceEnsureRequestCopyWith<$Res> {
  _$NamespaceEnsureRequestCopyWithImpl(this._self, this._then);

  final NamespaceEnsureRequest _self;
  final $Res Function(NamespaceEnsureRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? hostLabel = freezed,Object? endpoint = freezed,Object? authToken = freezed,Object? environmentConfigId = freezed,Object? interfacePackageId = freezed,Object? interfacePackageName = freezed,}) {
  return _then(NamespaceEnsureRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostLabel: freezed == hostLabel ? _self.hostLabel : hostLabel // ignore: cast_nullable_to_non_nullable
as String?,endpoint: freezed == endpoint ? _self.endpoint : endpoint // ignore: cast_nullable_to_non_nullable
as String?,authToken: freezed == authToken ? _self.authToken : authToken // ignore: cast_nullable_to_non_nullable
as String?,environmentConfigId: freezed == environmentConfigId ? _self.environmentConfigId : environmentConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfacePackageId: freezed == interfacePackageId ? _self.interfacePackageId : interfacePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfacePackageName: freezed == interfacePackageName ? _self.interfacePackageName : interfacePackageName // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class NamespaceListRequest implements InterfaceControlPlaneRequest {
   NamespaceListRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, final  String? $type}): $type = $type ?? 'namespace_list';
  factory NamespaceListRequest.fromJson(Map<String, dynamic> json) => _$NamespaceListRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NamespaceListRequestCopyWith<NamespaceListRequest> get copyWith => _$NamespaceListRequestCopyWithImpl<NamespaceListRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NamespaceListRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NamespaceListRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.namespaceList(requestId: $requestId, protocolVersion: $protocolVersion)';
}


}

/// @nodoc
abstract mixin class $NamespaceListRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $NamespaceListRequestCopyWith(NamespaceListRequest value, $Res Function(NamespaceListRequest) _then) = _$NamespaceListRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion
});




}
/// @nodoc
class _$NamespaceListRequestCopyWithImpl<$Res>
    implements $NamespaceListRequestCopyWith<$Res> {
  _$NamespaceListRequestCopyWithImpl(this._self, this._then);

  final NamespaceListRequest _self;
  final $Res Function(NamespaceListRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,}) {
  return _then(NamespaceListRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceStatusRequest implements InterfaceControlPlaneRequest {
   InterfaceStatusRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, final  String? $type}): $type = $type ?? 'interface_status';
  factory InterfaceStatusRequest.fromJson(Map<String, dynamic> json) => _$InterfaceStatusRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceStatusRequestCopyWith<InterfaceStatusRequest> get copyWith => _$InterfaceStatusRequestCopyWithImpl<InterfaceStatusRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceStatusRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceStatusRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceStatus(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace)';
}


}

/// @nodoc
abstract mixin class $InterfaceStatusRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceStatusRequestCopyWith(InterfaceStatusRequest value, $Res Function(InterfaceStatusRequest) _then) = _$InterfaceStatusRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace
});




}
/// @nodoc
class _$InterfaceStatusRequestCopyWithImpl<$Res>
    implements $InterfaceStatusRequestCopyWith<$Res> {
  _$InterfaceStatusRequestCopyWithImpl(this._self, this._then);

  final InterfaceStatusRequest _self;
  final $Res Function(InterfaceStatusRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,}) {
  return _then(InterfaceStatusRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceAdmitEnvironmentActorRequest implements InterfaceControlPlaneRequest {
   InterfaceAdmitEnvironmentActorRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() this.environmentId, @UuidValueConverter() required this.environmentProfileId, @UuidValueConverter() required this.actorConfigId, @UuidValueConverter() required this.classInstanceIdentityId, required this.objectInstanceGraphBranchKey, @UuidValueConverter() this.objectInstanceGraphBranchId, @UuidValueListConverter() final  List<UuidValue> requestedRoleConfigIds = const [], final  List<String> requestedRoleConfigNames = const [], this.reason, required final  Map<String, dynamic> evidence, final  String? $type}): _requestedRoleConfigIds = requestedRoleConfigIds,_requestedRoleConfigNames = requestedRoleConfigNames,_evidence = evidence,$type = $type ?? 'interface_admit_environment_actor';
  factory InterfaceAdmitEnvironmentActorRequest.fromJson(Map<String, dynamic> json) => _$InterfaceAdmitEnvironmentActorRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
@UuidValueConverter() final  UuidValue? environmentId;
@UuidValueConverter() final  UuidValue environmentProfileId;
@UuidValueConverter() final  UuidValue actorConfigId;
@UuidValueConverter() final  UuidValue classInstanceIdentityId;
 final  String objectInstanceGraphBranchKey;
@UuidValueConverter() final  UuidValue? objectInstanceGraphBranchId;
 final  List<UuidValue> _requestedRoleConfigIds;
@JsonKey()@UuidValueListConverter() List<UuidValue> get requestedRoleConfigIds {
  if (_requestedRoleConfigIds is EqualUnmodifiableListView) return _requestedRoleConfigIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requestedRoleConfigIds);
}

 final  List<String> _requestedRoleConfigNames;
@JsonKey() List<String> get requestedRoleConfigNames {
  if (_requestedRoleConfigNames is EqualUnmodifiableListView) return _requestedRoleConfigNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requestedRoleConfigNames);
}

 final  String? reason;
 final  Map<String, dynamic> _evidence;
 Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceAdmitEnvironmentActorRequestCopyWith<InterfaceAdmitEnvironmentActorRequest> get copyWith => _$InterfaceAdmitEnvironmentActorRequestCopyWithImpl<InterfaceAdmitEnvironmentActorRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceAdmitEnvironmentActorRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceAdmitEnvironmentActorRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.actorConfigId, actorConfigId) || other.actorConfigId == actorConfigId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&const DeepCollectionEquality().equals(other._requestedRoleConfigIds, _requestedRoleConfigIds)&&const DeepCollectionEquality().equals(other._requestedRoleConfigNames, _requestedRoleConfigNames)&&(identical(other.reason, reason) || other.reason == reason)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,environmentId,environmentProfileId,actorConfigId,classInstanceIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId,const DeepCollectionEquality().hash(_requestedRoleConfigIds),const DeepCollectionEquality().hash(_requestedRoleConfigNames),reason,const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceAdmitEnvironmentActor(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, environmentId: $environmentId, environmentProfileId: $environmentProfileId, actorConfigId: $actorConfigId, classInstanceIdentityId: $classInstanceIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, requestedRoleConfigIds: $requestedRoleConfigIds, requestedRoleConfigNames: $requestedRoleConfigNames, reason: $reason, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $InterfaceAdmitEnvironmentActorRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceAdmitEnvironmentActorRequestCopyWith(InterfaceAdmitEnvironmentActorRequest value, $Res Function(InterfaceAdmitEnvironmentActorRequest) _then) = _$InterfaceAdmitEnvironmentActorRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue environmentProfileId,@UuidValueConverter() UuidValue actorConfigId,@UuidValueConverter() UuidValue classInstanceIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueListConverter() List<UuidValue> requestedRoleConfigIds, List<String> requestedRoleConfigNames, String? reason, Map<String, dynamic> evidence
});




}
/// @nodoc
class _$InterfaceAdmitEnvironmentActorRequestCopyWithImpl<$Res>
    implements $InterfaceAdmitEnvironmentActorRequestCopyWith<$Res> {
  _$InterfaceAdmitEnvironmentActorRequestCopyWithImpl(this._self, this._then);

  final InterfaceAdmitEnvironmentActorRequest _self;
  final $Res Function(InterfaceAdmitEnvironmentActorRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? environmentId = freezed,Object? environmentProfileId = null,Object? actorConfigId = null,Object? classInstanceIdentityId = null,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,Object? requestedRoleConfigIds = null,Object? requestedRoleConfigNames = null,Object? reason = freezed,Object? evidence = null,}) {
  return _then(InterfaceAdmitEnvironmentActorRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentProfileId: null == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue,actorConfigId: null == actorConfigId ? _self.actorConfigId : actorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,classInstanceIdentityId: null == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedRoleConfigIds: null == requestedRoleConfigIds ? _self._requestedRoleConfigIds : requestedRoleConfigIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,requestedRoleConfigNames: null == requestedRoleConfigNames ? _self._requestedRoleConfigNames : requestedRoleConfigNames // ignore: cast_nullable_to_non_nullable
as List<String>,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceJoinEnvironmentSessionRequest implements InterfaceControlPlaneRequest {
   InterfaceJoinEnvironmentSessionRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() required this.environmentSessionId, @UuidValueConverter() this.environmentProfileId, this.environmentAdmissionReceipt, this.reason, required final  Map<String, dynamic> evidence, final  String? $type}): _evidence = evidence,$type = $type ?? 'interface_join_environment_session';
  factory InterfaceJoinEnvironmentSessionRequest.fromJson(Map<String, dynamic> json) => _$InterfaceJoinEnvironmentSessionRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
@UuidValueConverter() final  UuidValue environmentSessionId;
@UuidValueConverter() final  UuidValue? environmentProfileId;
 final  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt;
 final  String? reason;
 final  Map<String, dynamic> _evidence;
 Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceJoinEnvironmentSessionRequestCopyWith<InterfaceJoinEnvironmentSessionRequest> get copyWith => _$InterfaceJoinEnvironmentSessionRequestCopyWithImpl<InterfaceJoinEnvironmentSessionRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceJoinEnvironmentSessionRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceJoinEnvironmentSessionRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.environmentAdmissionReceipt, environmentAdmissionReceipt) || other.environmentAdmissionReceipt == environmentAdmissionReceipt)&&(identical(other.reason, reason) || other.reason == reason)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,environmentSessionId,environmentProfileId,environmentAdmissionReceipt,reason,const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceJoinEnvironmentSession(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, environmentSessionId: $environmentSessionId, environmentProfileId: $environmentProfileId, environmentAdmissionReceipt: $environmentAdmissionReceipt, reason: $reason, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $InterfaceJoinEnvironmentSessionRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceJoinEnvironmentSessionRequestCopyWith(InterfaceJoinEnvironmentSessionRequest value, $Res Function(InterfaceJoinEnvironmentSessionRequest) _then) = _$InterfaceJoinEnvironmentSessionRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue environmentSessionId,@UuidValueConverter() UuidValue? environmentProfileId, EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt, String? reason, Map<String, dynamic> evidence
});


$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt;

}
/// @nodoc
class _$InterfaceJoinEnvironmentSessionRequestCopyWithImpl<$Res>
    implements $InterfaceJoinEnvironmentSessionRequestCopyWith<$Res> {
  _$InterfaceJoinEnvironmentSessionRequestCopyWithImpl(this._self, this._then);

  final InterfaceJoinEnvironmentSessionRequest _self;
  final $Res Function(InterfaceJoinEnvironmentSessionRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? environmentSessionId = null,Object? environmentProfileId = freezed,Object? environmentAdmissionReceipt = freezed,Object? reason = freezed,Object? evidence = null,}) {
  return _then(InterfaceJoinEnvironmentSessionRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentSessionId: null == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,environmentProfileId: freezed == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentAdmissionReceipt: freezed == environmentAdmissionReceipt ? _self.environmentAdmissionReceipt : environmentAdmissionReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentActorAdmissionReceipt?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt {
    if (_self.environmentAdmissionReceipt == null) {
    return null;
  }

  return $EnvironmentActorAdmissionReceiptCopyWith<$Res>(_self.environmentAdmissionReceipt!, (value) {
    return _then(_self.copyWith(environmentAdmissionReceipt: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectEnvironmentNavigationTargetRequest implements InterfaceControlPlaneRequest {
   InterfaceSelectEnvironmentNavigationTargetRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() this.environmentNavigationContextId, @UuidValueConverter() this.selectedProcessId, @UuidValueConverter() this.selectedThreadId, this.reason, required final  Map<String, dynamic> evidence, final  String? $type}): _evidence = evidence,$type = $type ?? 'interface_select_environment_navigation_target';
  factory InterfaceSelectEnvironmentNavigationTargetRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSelectEnvironmentNavigationTargetRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
@UuidValueConverter() final  UuidValue? environmentNavigationContextId;
@UuidValueConverter() final  UuidValue? selectedProcessId;
@UuidValueConverter() final  UuidValue? selectedThreadId;
 final  String? reason;
 final  Map<String, dynamic> _evidence;
 Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectEnvironmentNavigationTargetRequestCopyWith<InterfaceSelectEnvironmentNavigationTargetRequest> get copyWith => _$InterfaceSelectEnvironmentNavigationTargetRequestCopyWithImpl<InterfaceSelectEnvironmentNavigationTargetRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectEnvironmentNavigationTargetRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectEnvironmentNavigationTargetRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentNavigationContextId, environmentNavigationContextId) || other.environmentNavigationContextId == environmentNavigationContextId)&&(identical(other.selectedProcessId, selectedProcessId) || other.selectedProcessId == selectedProcessId)&&(identical(other.selectedThreadId, selectedThreadId) || other.selectedThreadId == selectedThreadId)&&(identical(other.reason, reason) || other.reason == reason)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,environmentNavigationContextId,selectedProcessId,selectedThreadId,reason,const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceSelectEnvironmentNavigationTarget(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, environmentNavigationContextId: $environmentNavigationContextId, selectedProcessId: $selectedProcessId, selectedThreadId: $selectedThreadId, reason: $reason, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectEnvironmentNavigationTargetRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceSelectEnvironmentNavigationTargetRequestCopyWith(InterfaceSelectEnvironmentNavigationTargetRequest value, $Res Function(InterfaceSelectEnvironmentNavigationTargetRequest) _then) = _$InterfaceSelectEnvironmentNavigationTargetRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue? environmentNavigationContextId,@UuidValueConverter() UuidValue? selectedProcessId,@UuidValueConverter() UuidValue? selectedThreadId, String? reason, Map<String, dynamic> evidence
});




}
/// @nodoc
class _$InterfaceSelectEnvironmentNavigationTargetRequestCopyWithImpl<$Res>
    implements $InterfaceSelectEnvironmentNavigationTargetRequestCopyWith<$Res> {
  _$InterfaceSelectEnvironmentNavigationTargetRequestCopyWithImpl(this._self, this._then);

  final InterfaceSelectEnvironmentNavigationTargetRequest _self;
  final $Res Function(InterfaceSelectEnvironmentNavigationTargetRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? environmentNavigationContextId = freezed,Object? selectedProcessId = freezed,Object? selectedThreadId = freezed,Object? reason = freezed,Object? evidence = null,}) {
  return _then(InterfaceSelectEnvironmentNavigationTargetRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentNavigationContextId: freezed == environmentNavigationContextId ? _self.environmentNavigationContextId : environmentNavigationContextId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedProcessId: freezed == selectedProcessId ? _self.selectedProcessId : selectedProcessId // ignore: cast_nullable_to_non_nullable
as UuidValue?,selectedThreadId: freezed == selectedThreadId ? _self.selectedThreadId : selectedThreadId // ignore: cast_nullable_to_non_nullable
as UuidValue?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceEnterEnvironmentRequest implements InterfaceControlPlaneRequest {
   InterfaceEnterEnvironmentRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() this.environmentId, @UuidValueConverter() this.environmentProfileId, @UuidValueConverter() this.actorConfigId, @UuidValueConverter() this.classInstanceIdentityId, required this.objectInstanceGraphBranchKey, @UuidValueConverter() this.objectInstanceGraphBranchId, @UuidValueListConverter() final  List<UuidValue> requestedRoleConfigIds = const [], final  List<String> requestedRoleConfigNames = const [], this.environmentAdmissionReceipt, @UuidValueConverter() this.environmentSessionId, @UuidValueConverter() this.environmentSessionConfigId, this.sessionKey, this.title, this.description, this.purpose, this.sourceKind, this.sourceRef, this.reason, required final  Map<String, dynamic> evidence, final  String? $type}): _requestedRoleConfigIds = requestedRoleConfigIds,_requestedRoleConfigNames = requestedRoleConfigNames,_evidence = evidence,$type = $type ?? 'interface_enter_environment';
  factory InterfaceEnterEnvironmentRequest.fromJson(Map<String, dynamic> json) => _$InterfaceEnterEnvironmentRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
@UuidValueConverter() final  UuidValue? environmentId;
@UuidValueConverter() final  UuidValue? environmentProfileId;
@UuidValueConverter() final  UuidValue? actorConfigId;
@UuidValueConverter() final  UuidValue? classInstanceIdentityId;
 final  String objectInstanceGraphBranchKey;
@UuidValueConverter() final  UuidValue? objectInstanceGraphBranchId;
 final  List<UuidValue> _requestedRoleConfigIds;
@JsonKey()@UuidValueListConverter() List<UuidValue> get requestedRoleConfigIds {
  if (_requestedRoleConfigIds is EqualUnmodifiableListView) return _requestedRoleConfigIds;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requestedRoleConfigIds);
}

 final  List<String> _requestedRoleConfigNames;
@JsonKey() List<String> get requestedRoleConfigNames {
  if (_requestedRoleConfigNames is EqualUnmodifiableListView) return _requestedRoleConfigNames;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_requestedRoleConfigNames);
}

 final  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt;
@UuidValueConverter() final  UuidValue? environmentSessionId;
@UuidValueConverter() final  UuidValue? environmentSessionConfigId;
 final  String? sessionKey;
 final  String? title;
 final  String? description;
 final  String? purpose;
 final  String? sourceKind;
 final  String? sourceRef;
 final  String? reason;
 final  Map<String, dynamic> _evidence;
 Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceEnterEnvironmentRequestCopyWith<InterfaceEnterEnvironmentRequest> get copyWith => _$InterfaceEnterEnvironmentRequestCopyWithImpl<InterfaceEnterEnvironmentRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceEnterEnvironmentRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceEnterEnvironmentRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentId, environmentId) || other.environmentId == environmentId)&&(identical(other.environmentProfileId, environmentProfileId) || other.environmentProfileId == environmentProfileId)&&(identical(other.actorConfigId, actorConfigId) || other.actorConfigId == actorConfigId)&&(identical(other.classInstanceIdentityId, classInstanceIdentityId) || other.classInstanceIdentityId == classInstanceIdentityId)&&(identical(other.objectInstanceGraphBranchKey, objectInstanceGraphBranchKey) || other.objectInstanceGraphBranchKey == objectInstanceGraphBranchKey)&&(identical(other.objectInstanceGraphBranchId, objectInstanceGraphBranchId) || other.objectInstanceGraphBranchId == objectInstanceGraphBranchId)&&const DeepCollectionEquality().equals(other._requestedRoleConfigIds, _requestedRoleConfigIds)&&const DeepCollectionEquality().equals(other._requestedRoleConfigNames, _requestedRoleConfigNames)&&(identical(other.environmentAdmissionReceipt, environmentAdmissionReceipt) || other.environmentAdmissionReceipt == environmentAdmissionReceipt)&&(identical(other.environmentSessionId, environmentSessionId) || other.environmentSessionId == environmentSessionId)&&(identical(other.environmentSessionConfigId, environmentSessionConfigId) || other.environmentSessionConfigId == environmentSessionConfigId)&&(identical(other.sessionKey, sessionKey) || other.sessionKey == sessionKey)&&(identical(other.title, title) || other.title == title)&&(identical(other.description, description) || other.description == description)&&(identical(other.purpose, purpose) || other.purpose == purpose)&&(identical(other.sourceKind, sourceKind) || other.sourceKind == sourceKind)&&(identical(other.sourceRef, sourceRef) || other.sourceRef == sourceRef)&&(identical(other.reason, reason) || other.reason == reason)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,requestId,protocolVersion,namespace,environmentId,environmentProfileId,actorConfigId,classInstanceIdentityId,objectInstanceGraphBranchKey,objectInstanceGraphBranchId,const DeepCollectionEquality().hash(_requestedRoleConfigIds),const DeepCollectionEquality().hash(_requestedRoleConfigNames),environmentAdmissionReceipt,environmentSessionId,environmentSessionConfigId,sessionKey,title,description,purpose,sourceKind,sourceRef,reason,const DeepCollectionEquality().hash(_evidence)]);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceEnterEnvironment(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, environmentId: $environmentId, environmentProfileId: $environmentProfileId, actorConfigId: $actorConfigId, classInstanceIdentityId: $classInstanceIdentityId, objectInstanceGraphBranchKey: $objectInstanceGraphBranchKey, objectInstanceGraphBranchId: $objectInstanceGraphBranchId, requestedRoleConfigIds: $requestedRoleConfigIds, requestedRoleConfigNames: $requestedRoleConfigNames, environmentAdmissionReceipt: $environmentAdmissionReceipt, environmentSessionId: $environmentSessionId, environmentSessionConfigId: $environmentSessionConfigId, sessionKey: $sessionKey, title: $title, description: $description, purpose: $purpose, sourceKind: $sourceKind, sourceRef: $sourceRef, reason: $reason, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $InterfaceEnterEnvironmentRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceEnterEnvironmentRequestCopyWith(InterfaceEnterEnvironmentRequest value, $Res Function(InterfaceEnterEnvironmentRequest) _then) = _$InterfaceEnterEnvironmentRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue? environmentId,@UuidValueConverter() UuidValue? environmentProfileId,@UuidValueConverter() UuidValue? actorConfigId,@UuidValueConverter() UuidValue? classInstanceIdentityId, String objectInstanceGraphBranchKey,@UuidValueConverter() UuidValue? objectInstanceGraphBranchId,@UuidValueListConverter() List<UuidValue> requestedRoleConfigIds, List<String> requestedRoleConfigNames, EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,@UuidValueConverter() UuidValue? environmentSessionId,@UuidValueConverter() UuidValue? environmentSessionConfigId, String? sessionKey, String? title, String? description, String? purpose, String? sourceKind, String? sourceRef, String? reason, Map<String, dynamic> evidence
});


$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt;

}
/// @nodoc
class _$InterfaceEnterEnvironmentRequestCopyWithImpl<$Res>
    implements $InterfaceEnterEnvironmentRequestCopyWith<$Res> {
  _$InterfaceEnterEnvironmentRequestCopyWithImpl(this._self, this._then);

  final InterfaceEnterEnvironmentRequest _self;
  final $Res Function(InterfaceEnterEnvironmentRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? environmentId = freezed,Object? environmentProfileId = freezed,Object? actorConfigId = freezed,Object? classInstanceIdentityId = freezed,Object? objectInstanceGraphBranchKey = null,Object? objectInstanceGraphBranchId = freezed,Object? requestedRoleConfigIds = null,Object? requestedRoleConfigNames = null,Object? environmentAdmissionReceipt = freezed,Object? environmentSessionId = freezed,Object? environmentSessionConfigId = freezed,Object? sessionKey = freezed,Object? title = freezed,Object? description = freezed,Object? purpose = freezed,Object? sourceKind = freezed,Object? sourceRef = freezed,Object? reason = freezed,Object? evidence = null,}) {
  return _then(InterfaceEnterEnvironmentRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentId: freezed == environmentId ? _self.environmentId : environmentId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentProfileId: freezed == environmentProfileId ? _self.environmentProfileId : environmentProfileId // ignore: cast_nullable_to_non_nullable
as UuidValue?,actorConfigId: freezed == actorConfigId ? _self.actorConfigId : actorConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,classInstanceIdentityId: freezed == classInstanceIdentityId ? _self.classInstanceIdentityId : classInstanceIdentityId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphBranchKey: null == objectInstanceGraphBranchKey ? _self.objectInstanceGraphBranchKey : objectInstanceGraphBranchKey // ignore: cast_nullable_to_non_nullable
as String,objectInstanceGraphBranchId: freezed == objectInstanceGraphBranchId ? _self.objectInstanceGraphBranchId : objectInstanceGraphBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedRoleConfigIds: null == requestedRoleConfigIds ? _self._requestedRoleConfigIds : requestedRoleConfigIds // ignore: cast_nullable_to_non_nullable
as List<UuidValue>,requestedRoleConfigNames: null == requestedRoleConfigNames ? _self._requestedRoleConfigNames : requestedRoleConfigNames // ignore: cast_nullable_to_non_nullable
as List<String>,environmentAdmissionReceipt: freezed == environmentAdmissionReceipt ? _self.environmentAdmissionReceipt : environmentAdmissionReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentActorAdmissionReceipt?,environmentSessionId: freezed == environmentSessionId ? _self.environmentSessionId : environmentSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,environmentSessionConfigId: freezed == environmentSessionConfigId ? _self.environmentSessionConfigId : environmentSessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sessionKey: freezed == sessionKey ? _self.sessionKey : sessionKey // ignore: cast_nullable_to_non_nullable
as String?,title: freezed == title ? _self.title : title // ignore: cast_nullable_to_non_nullable
as String?,description: freezed == description ? _self.description : description // ignore: cast_nullable_to_non_nullable
as String?,purpose: freezed == purpose ? _self.purpose : purpose // ignore: cast_nullable_to_non_nullable
as String?,sourceKind: freezed == sourceKind ? _self.sourceKind : sourceKind // ignore: cast_nullable_to_non_nullable
as String?,sourceRef: freezed == sourceRef ? _self.sourceRef : sourceRef // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt {
    if (_self.environmentAdmissionReceipt == null) {
    return null;
  }

  return $EnvironmentActorAdmissionReceiptCopyWith<$Res>(_self.environmentAdmissionReceipt!, (value) {
    return _then(_self.copyWith(environmentAdmissionReceipt: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceResolveExperienceLensRequest implements InterfaceControlPlaneRequest {
   InterfaceResolveExperienceLensRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, this.environmentSessionJoinReceipt, this.environmentNavigationContext, this.experienceActorAdmission, @UuidValueConverter() this.experienceIdentitySessionConfigId, this.reason, required final  Map<String, dynamic> evidence, final  String? $type}): _evidence = evidence,$type = $type ?? 'interface_resolve_experience_lens';
  factory InterfaceResolveExperienceLensRequest.fromJson(Map<String, dynamic> json) => _$InterfaceResolveExperienceLensRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt;
 final  EnvironmentNavigationContextView? environmentNavigationContext;
 final  ExperienceActorConfigAdmissionReceipt? experienceActorAdmission;
@UuidValueConverter() final  UuidValue? experienceIdentitySessionConfigId;
 final  String? reason;
 final  Map<String, dynamic> _evidence;
 Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceResolveExperienceLensRequestCopyWith<InterfaceResolveExperienceLensRequest> get copyWith => _$InterfaceResolveExperienceLensRequestCopyWithImpl<InterfaceResolveExperienceLensRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceResolveExperienceLensRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceResolveExperienceLensRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentSessionJoinReceipt, environmentSessionJoinReceipt) || other.environmentSessionJoinReceipt == environmentSessionJoinReceipt)&&(identical(other.environmentNavigationContext, environmentNavigationContext) || other.environmentNavigationContext == environmentNavigationContext)&&(identical(other.experienceActorAdmission, experienceActorAdmission) || other.experienceActorAdmission == experienceActorAdmission)&&(identical(other.experienceIdentitySessionConfigId, experienceIdentitySessionConfigId) || other.experienceIdentitySessionConfigId == experienceIdentitySessionConfigId)&&(identical(other.reason, reason) || other.reason == reason)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,environmentSessionJoinReceipt,environmentNavigationContext,experienceActorAdmission,experienceIdentitySessionConfigId,reason,const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceResolveExperienceLens(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, environmentSessionJoinReceipt: $environmentSessionJoinReceipt, environmentNavigationContext: $environmentNavigationContext, experienceActorAdmission: $experienceActorAdmission, experienceIdentitySessionConfigId: $experienceIdentitySessionConfigId, reason: $reason, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $InterfaceResolveExperienceLensRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceResolveExperienceLensRequestCopyWith(InterfaceResolveExperienceLensRequest value, $Res Function(InterfaceResolveExperienceLensRequest) _then) = _$InterfaceResolveExperienceLensRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt, EnvironmentNavigationContextView? environmentNavigationContext, ExperienceActorConfigAdmissionReceipt? experienceActorAdmission,@UuidValueConverter() UuidValue? experienceIdentitySessionConfigId, String? reason, Map<String, dynamic> evidence
});


$EnvironmentSessionJoinReceiptCopyWith<$Res>? get environmentSessionJoinReceipt;$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext;$ExperienceActorConfigAdmissionReceiptCopyWith<$Res>? get experienceActorAdmission;

}
/// @nodoc
class _$InterfaceResolveExperienceLensRequestCopyWithImpl<$Res>
    implements $InterfaceResolveExperienceLensRequestCopyWith<$Res> {
  _$InterfaceResolveExperienceLensRequestCopyWithImpl(this._self, this._then);

  final InterfaceResolveExperienceLensRequest _self;
  final $Res Function(InterfaceResolveExperienceLensRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? environmentSessionJoinReceipt = freezed,Object? environmentNavigationContext = freezed,Object? experienceActorAdmission = freezed,Object? experienceIdentitySessionConfigId = freezed,Object? reason = freezed,Object? evidence = null,}) {
  return _then(InterfaceResolveExperienceLensRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentSessionJoinReceipt: freezed == environmentSessionJoinReceipt ? _self.environmentSessionJoinReceipt : environmentSessionJoinReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentSessionJoinReceipt?,environmentNavigationContext: freezed == environmentNavigationContext ? _self.environmentNavigationContext : environmentNavigationContext // ignore: cast_nullable_to_non_nullable
as EnvironmentNavigationContextView?,experienceActorAdmission: freezed == experienceActorAdmission ? _self.experienceActorAdmission : experienceActorAdmission // ignore: cast_nullable_to_non_nullable
as ExperienceActorConfigAdmissionReceipt?,experienceIdentitySessionConfigId: freezed == experienceIdentitySessionConfigId ? _self.experienceIdentitySessionConfigId : experienceIdentitySessionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentSessionJoinReceiptCopyWith<$Res>? get environmentSessionJoinReceipt {
    if (_self.environmentSessionJoinReceipt == null) {
    return null;
  }

  return $EnvironmentSessionJoinReceiptCopyWith<$Res>(_self.environmentSessionJoinReceipt!, (value) {
    return _then(_self.copyWith(environmentSessionJoinReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext {
    if (_self.environmentNavigationContext == null) {
    return null;
  }

  return $EnvironmentNavigationContextViewCopyWith<$Res>(_self.environmentNavigationContext!, (value) {
    return _then(_self.copyWith(environmentNavigationContext: value));
  });
}/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ExperienceActorConfigAdmissionReceiptCopyWith<$Res>? get experienceActorAdmission {
    if (_self.experienceActorAdmission == null) {
    return null;
  }

  return $ExperienceActorConfigAdmissionReceiptCopyWith<$Res>(_self.experienceActorAdmission!, (value) {
    return _then(_self.copyWith(experienceActorAdmission: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceActionRequest implements InterfaceControlPlaneRequest {
   InterfaceActionRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, this.paneRef, required this.actionKey, this.actionKind, this.operationRef, this.sdkOperationId, this.paneConfigSdkOperationId, this.endpointRef, this.apiCapabilityEndpointId, this.paneConfigApiCapabilityEndpointId, required final  Map<String, dynamic> payload, final  String? $type}): _payload = payload,$type = $type ?? 'interface_action';
  factory InterfaceActionRequest.fromJson(Map<String, dynamic> json) => _$InterfaceActionRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String? paneRef;
 final  String actionKey;
 final  String? actionKind;
 final  String? operationRef;
 final  String? sdkOperationId;
 final  String? paneConfigSdkOperationId;
 final  String? endpointRef;
 final  String? apiCapabilityEndpointId;
 final  String? paneConfigApiCapabilityEndpointId;
 final  Map<String, dynamic> _payload;
 Map<String, dynamic> get payload {
  if (_payload is EqualUnmodifiableMapView) return _payload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_payload);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceActionRequestCopyWith<InterfaceActionRequest> get copyWith => _$InterfaceActionRequestCopyWithImpl<InterfaceActionRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceActionRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceActionRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.paneRef, paneRef) || other.paneRef == paneRef)&&(identical(other.actionKey, actionKey) || other.actionKey == actionKey)&&(identical(other.actionKind, actionKind) || other.actionKind == actionKind)&&(identical(other.operationRef, operationRef) || other.operationRef == operationRef)&&(identical(other.sdkOperationId, sdkOperationId) || other.sdkOperationId == sdkOperationId)&&(identical(other.paneConfigSdkOperationId, paneConfigSdkOperationId) || other.paneConfigSdkOperationId == paneConfigSdkOperationId)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.paneConfigApiCapabilityEndpointId, paneConfigApiCapabilityEndpointId) || other.paneConfigApiCapabilityEndpointId == paneConfigApiCapabilityEndpointId)&&const DeepCollectionEquality().equals(other._payload, _payload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,paneRef,actionKey,actionKind,operationRef,sdkOperationId,paneConfigSdkOperationId,endpointRef,apiCapabilityEndpointId,paneConfigApiCapabilityEndpointId,const DeepCollectionEquality().hash(_payload));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceAction(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, paneRef: $paneRef, actionKey: $actionKey, actionKind: $actionKind, operationRef: $operationRef, sdkOperationId: $sdkOperationId, paneConfigSdkOperationId: $paneConfigSdkOperationId, endpointRef: $endpointRef, apiCapabilityEndpointId: $apiCapabilityEndpointId, paneConfigApiCapabilityEndpointId: $paneConfigApiCapabilityEndpointId, payload: $payload)';
}


}

/// @nodoc
abstract mixin class $InterfaceActionRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceActionRequestCopyWith(InterfaceActionRequest value, $Res Function(InterfaceActionRequest) _then) = _$InterfaceActionRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String? paneRef, String actionKey, String? actionKind, String? operationRef, String? sdkOperationId, String? paneConfigSdkOperationId, String? endpointRef, String? apiCapabilityEndpointId, String? paneConfigApiCapabilityEndpointId, Map<String, dynamic> payload
});




}
/// @nodoc
class _$InterfaceActionRequestCopyWithImpl<$Res>
    implements $InterfaceActionRequestCopyWith<$Res> {
  _$InterfaceActionRequestCopyWithImpl(this._self, this._then);

  final InterfaceActionRequest _self;
  final $Res Function(InterfaceActionRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? paneRef = freezed,Object? actionKey = null,Object? actionKind = freezed,Object? operationRef = freezed,Object? sdkOperationId = freezed,Object? paneConfigSdkOperationId = freezed,Object? endpointRef = freezed,Object? apiCapabilityEndpointId = freezed,Object? paneConfigApiCapabilityEndpointId = freezed,Object? payload = null,}) {
  return _then(InterfaceActionRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,paneRef: freezed == paneRef ? _self.paneRef : paneRef // ignore: cast_nullable_to_non_nullable
as String?,actionKey: null == actionKey ? _self.actionKey : actionKey // ignore: cast_nullable_to_non_nullable
as String,actionKind: freezed == actionKind ? _self.actionKind : actionKind // ignore: cast_nullable_to_non_nullable
as String?,operationRef: freezed == operationRef ? _self.operationRef : operationRef // ignore: cast_nullable_to_non_nullable
as String?,sdkOperationId: freezed == sdkOperationId ? _self.sdkOperationId : sdkOperationId // ignore: cast_nullable_to_non_nullable
as String?,paneConfigSdkOperationId: freezed == paneConfigSdkOperationId ? _self.paneConfigSdkOperationId : paneConfigSdkOperationId // ignore: cast_nullable_to_non_nullable
as String?,endpointRef: freezed == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String?,apiCapabilityEndpointId: freezed == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as String?,paneConfigApiCapabilityEndpointId: freezed == paneConfigApiCapabilityEndpointId ? _self.paneConfigApiCapabilityEndpointId : paneConfigApiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as String?,payload: null == payload ? _self._payload : payload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectStepRequest implements InterfaceControlPlaneRequest {
   InterfaceSelectStepRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, this.stepId, final  String? $type}): $type = $type ?? 'interface_select_step';
  factory InterfaceSelectStepRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSelectStepRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String? stepId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectStepRequestCopyWith<InterfaceSelectStepRequest> get copyWith => _$InterfaceSelectStepRequestCopyWithImpl<InterfaceSelectStepRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectStepRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectStepRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.stepId, stepId) || other.stepId == stepId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,stepId);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceSelectStep(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, stepId: $stepId)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectStepRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceSelectStepRequestCopyWith(InterfaceSelectStepRequest value, $Res Function(InterfaceSelectStepRequest) _then) = _$InterfaceSelectStepRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String? stepId
});




}
/// @nodoc
class _$InterfaceSelectStepRequestCopyWithImpl<$Res>
    implements $InterfaceSelectStepRequestCopyWith<$Res> {
  _$InterfaceSelectStepRequestCopyWithImpl(this._self, this._then);

  final InterfaceSelectStepRequest _self;
  final $Res Function(InterfaceSelectStepRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? stepId = freezed,}) {
  return _then(InterfaceSelectStepRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,stepId: freezed == stepId ? _self.stepId : stepId // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectProfileRequest implements InterfaceControlPlaneRequest {
   InterfaceSelectProfileRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, required this.profileId, final  String? $type}): $type = $type ?? 'interface_select_profile';
  factory InterfaceSelectProfileRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSelectProfileRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String profileId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectProfileRequestCopyWith<InterfaceSelectProfileRequest> get copyWith => _$InterfaceSelectProfileRequestCopyWithImpl<InterfaceSelectProfileRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectProfileRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectProfileRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.profileId, profileId) || other.profileId == profileId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,profileId);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceSelectProfile(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, profileId: $profileId)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectProfileRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceSelectProfileRequestCopyWith(InterfaceSelectProfileRequest value, $Res Function(InterfaceSelectProfileRequest) _then) = _$InterfaceSelectProfileRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String profileId
});




}
/// @nodoc
class _$InterfaceSelectProfileRequestCopyWithImpl<$Res>
    implements $InterfaceSelectProfileRequestCopyWith<$Res> {
  _$InterfaceSelectProfileRequestCopyWithImpl(this._self, this._then);

  final InterfaceSelectProfileRequest _self;
  final $Res Function(InterfaceSelectProfileRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? profileId = null,}) {
  return _then(InterfaceSelectProfileRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,profileId: null == profileId ? _self.profileId : profileId // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectRuntimeLayoutRequest implements InterfaceControlPlaneRequest {
   InterfaceSelectRuntimeLayoutRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() this.layoutConfigId, final  String? $type}): $type = $type ?? 'interface_select_runtime_layout';
  factory InterfaceSelectRuntimeLayoutRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSelectRuntimeLayoutRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
@UuidValueConverter() final  UuidValue? layoutConfigId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectRuntimeLayoutRequestCopyWith<InterfaceSelectRuntimeLayoutRequest> get copyWith => _$InterfaceSelectRuntimeLayoutRequestCopyWithImpl<InterfaceSelectRuntimeLayoutRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectRuntimeLayoutRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectRuntimeLayoutRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,layoutConfigId);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceSelectRuntimeLayout(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, layoutConfigId: $layoutConfigId)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectRuntimeLayoutRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceSelectRuntimeLayoutRequestCopyWith(InterfaceSelectRuntimeLayoutRequest value, $Res Function(InterfaceSelectRuntimeLayoutRequest) _then) = _$InterfaceSelectRuntimeLayoutRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue? layoutConfigId
});




}
/// @nodoc
class _$InterfaceSelectRuntimeLayoutRequestCopyWithImpl<$Res>
    implements $InterfaceSelectRuntimeLayoutRequestCopyWith<$Res> {
  _$InterfaceSelectRuntimeLayoutRequestCopyWithImpl(this._self, this._then);

  final InterfaceSelectRuntimeLayoutRequest _self;
  final $Res Function(InterfaceSelectRuntimeLayoutRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? layoutConfigId = freezed,}) {
  return _then(InterfaceSelectRuntimeLayoutRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,layoutConfigId: freezed == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceActivateRuntimeFocusRequest implements InterfaceControlPlaneRequest {
   InterfaceActivateRuntimeFocusRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() this.representationId, final  String? $type}): $type = $type ?? 'interface_activate_runtime_focus';
  factory InterfaceActivateRuntimeFocusRequest.fromJson(Map<String, dynamic> json) => _$InterfaceActivateRuntimeFocusRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
@UuidValueConverter() final  UuidValue? representationId;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceActivateRuntimeFocusRequestCopyWith<InterfaceActivateRuntimeFocusRequest> get copyWith => _$InterfaceActivateRuntimeFocusRequestCopyWithImpl<InterfaceActivateRuntimeFocusRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceActivateRuntimeFocusRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceActivateRuntimeFocusRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.representationId, representationId) || other.representationId == representationId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,representationId);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceActivateRuntimeFocus(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, representationId: $representationId)';
}


}

/// @nodoc
abstract mixin class $InterfaceActivateRuntimeFocusRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceActivateRuntimeFocusRequestCopyWith(InterfaceActivateRuntimeFocusRequest value, $Res Function(InterfaceActivateRuntimeFocusRequest) _then) = _$InterfaceActivateRuntimeFocusRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue? representationId
});




}
/// @nodoc
class _$InterfaceActivateRuntimeFocusRequestCopyWithImpl<$Res>
    implements $InterfaceActivateRuntimeFocusRequestCopyWith<$Res> {
  _$InterfaceActivateRuntimeFocusRequestCopyWithImpl(this._self, this._then);

  final InterfaceActivateRuntimeFocusRequest _self;
  final $Res Function(InterfaceActivateRuntimeFocusRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? representationId = freezed,}) {
  return _then(InterfaceActivateRuntimeFocusRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,representationId: freezed == representationId ? _self.representationId : representationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceRequestWindowLayoutRequest implements InterfaceControlPlaneRequest {
   InterfaceRequestWindowLayoutRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() this.interfacePackageId, this.interfacePackageName, this.windowKey, @UuidValueConverter() this.layoutConfigId, this.layoutKey, this.sectionKey, @UuidValueConverter() this.observableId, @UuidValueConverter() this.representationId, this.requestedByService, this.requestedByOperation, this.reason, this.idempotencyKey, final  String? $type}): $type = $type ?? 'interface_request_window_layout';
  factory InterfaceRequestWindowLayoutRequest.fromJson(Map<String, dynamic> json) => _$InterfaceRequestWindowLayoutRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
@UuidValueConverter() final  UuidValue? interfacePackageId;
 final  String? interfacePackageName;
 final  String? windowKey;
@UuidValueConverter() final  UuidValue? layoutConfigId;
 final  String? layoutKey;
 final  String? sectionKey;
@UuidValueConverter() final  UuidValue? observableId;
@UuidValueConverter() final  UuidValue? representationId;
 final  String? requestedByService;
 final  String? requestedByOperation;
 final  String? reason;
 final  String? idempotencyKey;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceRequestWindowLayoutRequestCopyWith<InterfaceRequestWindowLayoutRequest> get copyWith => _$InterfaceRequestWindowLayoutRequestCopyWithImpl<InterfaceRequestWindowLayoutRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceRequestWindowLayoutRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceRequestWindowLayoutRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.interfacePackageId, interfacePackageId) || other.interfacePackageId == interfacePackageId)&&(identical(other.interfacePackageName, interfacePackageName) || other.interfacePackageName == interfacePackageName)&&(identical(other.windowKey, windowKey) || other.windowKey == windowKey)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.layoutKey, layoutKey) || other.layoutKey == layoutKey)&&(identical(other.sectionKey, sectionKey) || other.sectionKey == sectionKey)&&(identical(other.observableId, observableId) || other.observableId == observableId)&&(identical(other.representationId, representationId) || other.representationId == representationId)&&(identical(other.requestedByService, requestedByService) || other.requestedByService == requestedByService)&&(identical(other.requestedByOperation, requestedByOperation) || other.requestedByOperation == requestedByOperation)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,interfacePackageId,interfacePackageName,windowKey,layoutConfigId,layoutKey,sectionKey,observableId,representationId,requestedByService,requestedByOperation,reason,idempotencyKey);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceRequestWindowLayout(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, interfacePackageId: $interfacePackageId, interfacePackageName: $interfacePackageName, windowKey: $windowKey, layoutConfigId: $layoutConfigId, layoutKey: $layoutKey, sectionKey: $sectionKey, observableId: $observableId, representationId: $representationId, requestedByService: $requestedByService, requestedByOperation: $requestedByOperation, reason: $reason, idempotencyKey: $idempotencyKey)';
}


}

/// @nodoc
abstract mixin class $InterfaceRequestWindowLayoutRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceRequestWindowLayoutRequestCopyWith(InterfaceRequestWindowLayoutRequest value, $Res Function(InterfaceRequestWindowLayoutRequest) _then) = _$InterfaceRequestWindowLayoutRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue? interfacePackageId, String? interfacePackageName, String? windowKey,@UuidValueConverter() UuidValue? layoutConfigId, String? layoutKey, String? sectionKey,@UuidValueConverter() UuidValue? observableId,@UuidValueConverter() UuidValue? representationId, String? requestedByService, String? requestedByOperation, String? reason, String? idempotencyKey
});




}
/// @nodoc
class _$InterfaceRequestWindowLayoutRequestCopyWithImpl<$Res>
    implements $InterfaceRequestWindowLayoutRequestCopyWith<$Res> {
  _$InterfaceRequestWindowLayoutRequestCopyWithImpl(this._self, this._then);

  final InterfaceRequestWindowLayoutRequest _self;
  final $Res Function(InterfaceRequestWindowLayoutRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? interfacePackageId = freezed,Object? interfacePackageName = freezed,Object? windowKey = freezed,Object? layoutConfigId = freezed,Object? layoutKey = freezed,Object? sectionKey = freezed,Object? observableId = freezed,Object? representationId = freezed,Object? requestedByService = freezed,Object? requestedByOperation = freezed,Object? reason = freezed,Object? idempotencyKey = freezed,}) {
  return _then(InterfaceRequestWindowLayoutRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,interfacePackageId: freezed == interfacePackageId ? _self.interfacePackageId : interfacePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfacePackageName: freezed == interfacePackageName ? _self.interfacePackageName : interfacePackageName // ignore: cast_nullable_to_non_nullable
as String?,windowKey: freezed == windowKey ? _self.windowKey : windowKey // ignore: cast_nullable_to_non_nullable
as String?,layoutConfigId: freezed == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutKey: freezed == layoutKey ? _self.layoutKey : layoutKey // ignore: cast_nullable_to_non_nullable
as String?,sectionKey: freezed == sectionKey ? _self.sectionKey : sectionKey // ignore: cast_nullable_to_non_nullable
as String?,observableId: freezed == observableId ? _self.observableId : observableId // ignore: cast_nullable_to_non_nullable
as UuidValue?,representationId: freezed == representationId ? _self.representationId : representationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedByService: freezed == requestedByService ? _self.requestedByService : requestedByService // ignore: cast_nullable_to_non_nullable
as String?,requestedByOperation: freezed == requestedByOperation ? _self.requestedByOperation : requestedByOperation // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceApplyAttentionLayoutTransitionRequest implements InterfaceControlPlaneRequest {
   InterfaceApplyAttentionLayoutTransitionRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, required this.clientIntentId, @UuidValueConverter() this.expectedPreviousLayoutTransitionId, @UuidValueConverter() this.topologyTransitionId, final  List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates = const [], final  String? $type}): _sectionStates = sectionStates,$type = $type ?? 'interface_apply_attention_layout_transition';
  factory InterfaceApplyAttentionLayoutTransitionRequest.fromJson(Map<String, dynamic> json) => _$InterfaceApplyAttentionLayoutTransitionRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String clientIntentId;
@UuidValueConverter() final  UuidValue? expectedPreviousLayoutTransitionId;
@UuidValueConverter() final  UuidValue? topologyTransitionId;
 final  List<InterfaceAttentionLayoutTransitionSectionIntent> _sectionStates;
@JsonKey() List<InterfaceAttentionLayoutTransitionSectionIntent> get sectionStates {
  if (_sectionStates is EqualUnmodifiableListView) return _sectionStates;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sectionStates);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceApplyAttentionLayoutTransitionRequestCopyWith<InterfaceApplyAttentionLayoutTransitionRequest> get copyWith => _$InterfaceApplyAttentionLayoutTransitionRequestCopyWithImpl<InterfaceApplyAttentionLayoutTransitionRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceApplyAttentionLayoutTransitionRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceApplyAttentionLayoutTransitionRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.clientIntentId, clientIntentId) || other.clientIntentId == clientIntentId)&&(identical(other.expectedPreviousLayoutTransitionId, expectedPreviousLayoutTransitionId) || other.expectedPreviousLayoutTransitionId == expectedPreviousLayoutTransitionId)&&(identical(other.topologyTransitionId, topologyTransitionId) || other.topologyTransitionId == topologyTransitionId)&&const DeepCollectionEquality().equals(other._sectionStates, _sectionStates));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,clientIntentId,expectedPreviousLayoutTransitionId,topologyTransitionId,const DeepCollectionEquality().hash(_sectionStates));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceApplyAttentionLayoutTransition(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, clientIntentId: $clientIntentId, expectedPreviousLayoutTransitionId: $expectedPreviousLayoutTransitionId, topologyTransitionId: $topologyTransitionId, sectionStates: $sectionStates)';
}


}

/// @nodoc
abstract mixin class $InterfaceApplyAttentionLayoutTransitionRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceApplyAttentionLayoutTransitionRequestCopyWith(InterfaceApplyAttentionLayoutTransitionRequest value, $Res Function(InterfaceApplyAttentionLayoutTransitionRequest) _then) = _$InterfaceApplyAttentionLayoutTransitionRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String clientIntentId,@UuidValueConverter() UuidValue? expectedPreviousLayoutTransitionId,@UuidValueConverter() UuidValue? topologyTransitionId, List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates
});




}
/// @nodoc
class _$InterfaceApplyAttentionLayoutTransitionRequestCopyWithImpl<$Res>
    implements $InterfaceApplyAttentionLayoutTransitionRequestCopyWith<$Res> {
  _$InterfaceApplyAttentionLayoutTransitionRequestCopyWithImpl(this._self, this._then);

  final InterfaceApplyAttentionLayoutTransitionRequest _self;
  final $Res Function(InterfaceApplyAttentionLayoutTransitionRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? clientIntentId = null,Object? expectedPreviousLayoutTransitionId = freezed,Object? topologyTransitionId = freezed,Object? sectionStates = null,}) {
  return _then(InterfaceApplyAttentionLayoutTransitionRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,clientIntentId: null == clientIntentId ? _self.clientIntentId : clientIntentId // ignore: cast_nullable_to_non_nullable
as String,expectedPreviousLayoutTransitionId: freezed == expectedPreviousLayoutTransitionId ? _self.expectedPreviousLayoutTransitionId : expectedPreviousLayoutTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,topologyTransitionId: freezed == topologyTransitionId ? _self.topologyTransitionId : topologyTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionStates: null == sectionStates ? _self._sectionStates : sectionStates // ignore: cast_nullable_to_non_nullable
as List<InterfaceAttentionLayoutTransitionSectionIntent>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceApplyAttentionLayoutTopologyTransitionRequest implements InterfaceControlPlaneRequest {
   InterfaceApplyAttentionLayoutTopologyTransitionRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, required this.clientIntentId, @UuidValueConverter() this.expectedPreviousTopologyTransitionId, final  List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates = const [], final  String? $type}): _sectionStates = sectionStates,$type = $type ?? 'interface_apply_attention_layout_topology_transition';
  factory InterfaceApplyAttentionLayoutTopologyTransitionRequest.fromJson(Map<String, dynamic> json) => _$InterfaceApplyAttentionLayoutTopologyTransitionRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String clientIntentId;
@UuidValueConverter() final  UuidValue? expectedPreviousTopologyTransitionId;
 final  List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> _sectionStates;
@JsonKey() List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> get sectionStates {
  if (_sectionStates is EqualUnmodifiableListView) return _sectionStates;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_sectionStates);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWith<InterfaceApplyAttentionLayoutTopologyTransitionRequest> get copyWith => _$InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWithImpl<InterfaceApplyAttentionLayoutTopologyTransitionRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceApplyAttentionLayoutTopologyTransitionRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceApplyAttentionLayoutTopologyTransitionRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.clientIntentId, clientIntentId) || other.clientIntentId == clientIntentId)&&(identical(other.expectedPreviousTopologyTransitionId, expectedPreviousTopologyTransitionId) || other.expectedPreviousTopologyTransitionId == expectedPreviousTopologyTransitionId)&&const DeepCollectionEquality().equals(other._sectionStates, _sectionStates));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,clientIntentId,expectedPreviousTopologyTransitionId,const DeepCollectionEquality().hash(_sectionStates));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceApplyAttentionLayoutTopologyTransition(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, clientIntentId: $clientIntentId, expectedPreviousTopologyTransitionId: $expectedPreviousTopologyTransitionId, sectionStates: $sectionStates)';
}


}

/// @nodoc
abstract mixin class $InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWith(InterfaceApplyAttentionLayoutTopologyTransitionRequest value, $Res Function(InterfaceApplyAttentionLayoutTopologyTransitionRequest) _then) = _$InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String clientIntentId,@UuidValueConverter() UuidValue? expectedPreviousTopologyTransitionId, List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates
});




}
/// @nodoc
class _$InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWithImpl<$Res>
    implements $InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWith<$Res> {
  _$InterfaceApplyAttentionLayoutTopologyTransitionRequestCopyWithImpl(this._self, this._then);

  final InterfaceApplyAttentionLayoutTopologyTransitionRequest _self;
  final $Res Function(InterfaceApplyAttentionLayoutTopologyTransitionRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? clientIntentId = null,Object? expectedPreviousTopologyTransitionId = freezed,Object? sectionStates = null,}) {
  return _then(InterfaceApplyAttentionLayoutTopologyTransitionRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,clientIntentId: null == clientIntentId ? _self.clientIntentId : clientIntentId // ignore: cast_nullable_to_non_nullable
as String,expectedPreviousTopologyTransitionId: freezed == expectedPreviousTopologyTransitionId ? _self.expectedPreviousTopologyTransitionId : expectedPreviousTopologyTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,sectionStates: null == sectionStates ? _self._sectionStates : sectionStates // ignore: cast_nullable_to_non_nullable
as List<InterfaceAttentionLayoutTopologyTransitionSectionIntent>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceReportRendererCapabilitiesRequest implements InterfaceControlPlaneRequest {
   InterfaceReportRendererCapabilitiesRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, required this.rendererCapabilities, final  String? $type}): $type = $type ?? 'interface_report_renderer_capabilities';
  factory InterfaceReportRendererCapabilitiesRequest.fromJson(Map<String, dynamic> json) => _$InterfaceReportRendererCapabilitiesRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  InterfaceRendererCapabilitiesState rendererCapabilities;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceReportRendererCapabilitiesRequestCopyWith<InterfaceReportRendererCapabilitiesRequest> get copyWith => _$InterfaceReportRendererCapabilitiesRequestCopyWithImpl<InterfaceReportRendererCapabilitiesRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceReportRendererCapabilitiesRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceReportRendererCapabilitiesRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.rendererCapabilities, rendererCapabilities) || other.rendererCapabilities == rendererCapabilities));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,rendererCapabilities);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceReportRendererCapabilities(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, rendererCapabilities: $rendererCapabilities)';
}


}

/// @nodoc
abstract mixin class $InterfaceReportRendererCapabilitiesRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceReportRendererCapabilitiesRequestCopyWith(InterfaceReportRendererCapabilitiesRequest value, $Res Function(InterfaceReportRendererCapabilitiesRequest) _then) = _$InterfaceReportRendererCapabilitiesRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, InterfaceRendererCapabilitiesState rendererCapabilities
});


$InterfaceRendererCapabilitiesStateCopyWith<$Res> get rendererCapabilities;

}
/// @nodoc
class _$InterfaceReportRendererCapabilitiesRequestCopyWithImpl<$Res>
    implements $InterfaceReportRendererCapabilitiesRequestCopyWith<$Res> {
  _$InterfaceReportRendererCapabilitiesRequestCopyWithImpl(this._self, this._then);

  final InterfaceReportRendererCapabilitiesRequest _self;
  final $Res Function(InterfaceReportRendererCapabilitiesRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? rendererCapabilities = null,}) {
  return _then(InterfaceReportRendererCapabilitiesRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,rendererCapabilities: null == rendererCapabilities ? _self.rendererCapabilities : rendererCapabilities // ignore: cast_nullable_to_non_nullable
as InterfaceRendererCapabilitiesState,
  ));
}

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceRendererCapabilitiesStateCopyWith<$Res> get rendererCapabilities {
  
  return $InterfaceRendererCapabilitiesStateCopyWith<$Res>(_self.rendererCapabilities, (value) {
    return _then(_self.copyWith(rendererCapabilities: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSyncViewStateCursorRequest implements InterfaceControlPlaneRequest {
   InterfaceSyncViewStateCursorRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, this.rendererId, this.knownCursor, this.knownDigest, final  String? $type}): $type = $type ?? 'interface_sync_view_state_cursor';
  factory InterfaceSyncViewStateCursorRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSyncViewStateCursorRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String? rendererId;
 final  String? knownCursor;
 final  String? knownDigest;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSyncViewStateCursorRequestCopyWith<InterfaceSyncViewStateCursorRequest> get copyWith => _$InterfaceSyncViewStateCursorRequestCopyWithImpl<InterfaceSyncViewStateCursorRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSyncViewStateCursorRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSyncViewStateCursorRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.rendererId, rendererId) || other.rendererId == rendererId)&&(identical(other.knownCursor, knownCursor) || other.knownCursor == knownCursor)&&(identical(other.knownDigest, knownDigest) || other.knownDigest == knownDigest));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,rendererId,knownCursor,knownDigest);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceSyncViewStateCursor(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, rendererId: $rendererId, knownCursor: $knownCursor, knownDigest: $knownDigest)';
}


}

/// @nodoc
abstract mixin class $InterfaceSyncViewStateCursorRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceSyncViewStateCursorRequestCopyWith(InterfaceSyncViewStateCursorRequest value, $Res Function(InterfaceSyncViewStateCursorRequest) _then) = _$InterfaceSyncViewStateCursorRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String? rendererId, String? knownCursor, String? knownDigest
});




}
/// @nodoc
class _$InterfaceSyncViewStateCursorRequestCopyWithImpl<$Res>
    implements $InterfaceSyncViewStateCursorRequestCopyWith<$Res> {
  _$InterfaceSyncViewStateCursorRequestCopyWithImpl(this._self, this._then);

  final InterfaceSyncViewStateCursorRequest _self;
  final $Res Function(InterfaceSyncViewStateCursorRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? rendererId = freezed,Object? knownCursor = freezed,Object? knownDigest = freezed,}) {
  return _then(InterfaceSyncViewStateCursorRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,rendererId: freezed == rendererId ? _self.rendererId : rendererId // ignore: cast_nullable_to_non_nullable
as String?,knownCursor: freezed == knownCursor ? _self.knownCursor : knownCursor // ignore: cast_nullable_to_non_nullable
as String?,knownDigest: freezed == knownDigest ? _self.knownDigest : knownDigest // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceFollowRequest implements InterfaceControlPlaneRequest {
   InterfaceFollowRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, required this.pollIntervalMs, final  String? $type}): $type = $type ?? 'interface_follow';
  factory InterfaceFollowRequest.fromJson(Map<String, dynamic> json) => _$InterfaceFollowRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  int pollIntervalMs;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceFollowRequestCopyWith<InterfaceFollowRequest> get copyWith => _$InterfaceFollowRequestCopyWithImpl<InterfaceFollowRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceFollowRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceFollowRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.pollIntervalMs, pollIntervalMs) || other.pollIntervalMs == pollIntervalMs));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,pollIntervalMs);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceFollow(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, pollIntervalMs: $pollIntervalMs)';
}


}

/// @nodoc
abstract mixin class $InterfaceFollowRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceFollowRequestCopyWith(InterfaceFollowRequest value, $Res Function(InterfaceFollowRequest) _then) = _$InterfaceFollowRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, int pollIntervalMs
});




}
/// @nodoc
class _$InterfaceFollowRequestCopyWithImpl<$Res>
    implements $InterfaceFollowRequestCopyWith<$Res> {
  _$InterfaceFollowRequestCopyWithImpl(this._self, this._then);

  final InterfaceFollowRequest _self;
  final $Res Function(InterfaceFollowRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? pollIntervalMs = null,}) {
  return _then(InterfaceFollowRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,pollIntervalMs: null == pollIntervalMs ? _self.pollIntervalMs : pollIntervalMs // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceInvokeApiRequest implements InterfaceControlPlaneRequest {
   InterfaceInvokeApiRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, required this.endpointRef, required this.discriminant, required final  Map<String, dynamic> requestPayload, final  String? $type}): _requestPayload = requestPayload,$type = $type ?? 'interface_invoke_api';
  factory InterfaceInvokeApiRequest.fromJson(Map<String, dynamic> json) => _$InterfaceInvokeApiRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String endpointRef;
 final  String discriminant;
 final  Map<String, dynamic> _requestPayload;
 Map<String, dynamic> get requestPayload {
  if (_requestPayload is EqualUnmodifiableMapView) return _requestPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_requestPayload);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceInvokeApiRequestCopyWith<InterfaceInvokeApiRequest> get copyWith => _$InterfaceInvokeApiRequestCopyWithImpl<InterfaceInvokeApiRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceInvokeApiRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceInvokeApiRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&const DeepCollectionEquality().equals(other._requestPayload, _requestPayload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,endpointRef,discriminant,const DeepCollectionEquality().hash(_requestPayload));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceInvokeApi(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, endpointRef: $endpointRef, discriminant: $discriminant, requestPayload: $requestPayload)';
}


}

/// @nodoc
abstract mixin class $InterfaceInvokeApiRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceInvokeApiRequestCopyWith(InterfaceInvokeApiRequest value, $Res Function(InterfaceInvokeApiRequest) _then) = _$InterfaceInvokeApiRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String endpointRef, String discriminant, Map<String, dynamic> requestPayload
});




}
/// @nodoc
class _$InterfaceInvokeApiRequestCopyWithImpl<$Res>
    implements $InterfaceInvokeApiRequestCopyWith<$Res> {
  _$InterfaceInvokeApiRequestCopyWithImpl(this._self, this._then);

  final InterfaceInvokeApiRequest _self;
  final $Res Function(InterfaceInvokeApiRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? endpointRef = null,Object? discriminant = null,Object? requestPayload = null,}) {
  return _then(InterfaceInvokeApiRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,requestPayload: null == requestPayload ? _self._requestPayload : requestPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceStreamApiRequest implements InterfaceControlPlaneRequest {
   InterfaceStreamApiRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, required this.endpointRef, required this.discriminant, required final  Map<String, dynamic> requestPayload, final  String? $type}): _requestPayload = requestPayload,$type = $type ?? 'interface_stream_api';
  factory InterfaceStreamApiRequest.fromJson(Map<String, dynamic> json) => _$InterfaceStreamApiRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;
 final  String endpointRef;
 final  String discriminant;
 final  Map<String, dynamic> _requestPayload;
 Map<String, dynamic> get requestPayload {
  if (_requestPayload is EqualUnmodifiableMapView) return _requestPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_requestPayload);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceStreamApiRequestCopyWith<InterfaceStreamApiRequest> get copyWith => _$InterfaceStreamApiRequestCopyWithImpl<InterfaceStreamApiRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceStreamApiRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceStreamApiRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&const DeepCollectionEquality().equals(other._requestPayload, _requestPayload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace,endpointRef,discriminant,const DeepCollectionEquality().hash(_requestPayload));

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceStreamApi(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, endpointRef: $endpointRef, discriminant: $discriminant, requestPayload: $requestPayload)';
}


}

/// @nodoc
abstract mixin class $InterfaceStreamApiRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceStreamApiRequestCopyWith(InterfaceStreamApiRequest value, $Res Function(InterfaceStreamApiRequest) _then) = _$InterfaceStreamApiRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace, String endpointRef, String discriminant, Map<String, dynamic> requestPayload
});




}
/// @nodoc
class _$InterfaceStreamApiRequestCopyWithImpl<$Res>
    implements $InterfaceStreamApiRequestCopyWith<$Res> {
  _$InterfaceStreamApiRequestCopyWithImpl(this._self, this._then);

  final InterfaceStreamApiRequest _self;
  final $Res Function(InterfaceStreamApiRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? endpointRef = null,Object? discriminant = null,Object? requestPayload = null,}) {
  return _then(InterfaceStreamApiRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,requestPayload: null == requestPayload ? _self._requestPayload : requestPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceStopRequest implements InterfaceControlPlaneRequest {
   InterfaceStopRequest({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, final  String? $type}): $type = $type ?? 'interface_stop';
  factory InterfaceStopRequest.fromJson(Map<String, dynamic> json) => _$InterfaceStopRequestFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
 final  String namespace;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceStopRequestCopyWith<InterfaceStopRequest> get copyWith => _$InterfaceStopRequestCopyWithImpl<InterfaceStopRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceStopRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceStopRequest&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,namespace);

@override
String toString() {
  return 'InterfaceControlPlaneRequest.interfaceStop(requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace)';
}


}

/// @nodoc
abstract mixin class $InterfaceStopRequestCopyWith<$Res> implements $InterfaceControlPlaneRequestCopyWith<$Res> {
  factory $InterfaceStopRequestCopyWith(InterfaceStopRequest value, $Res Function(InterfaceStopRequest) _then) = _$InterfaceStopRequestCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace
});




}
/// @nodoc
class _$InterfaceStopRequestCopyWithImpl<$Res>
    implements $InterfaceStopRequestCopyWith<$Res> {
  _$InterfaceStopRequestCopyWithImpl(this._self, this._then);

  final InterfaceStopRequest _self;
  final $Res Function(InterfaceStopRequest) _then;

/// Create a copy of InterfaceControlPlaneRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,}) {
  return _then(InterfaceStopRequest(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

InterfaceControlPlaneResponse _$InterfaceControlPlaneResponseFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'ping':
          return PingResponse.fromJson(
            json
          );
                case 'namespace_ensure':
          return NamespaceEnsureResponse.fromJson(
            json
          );
                case 'namespace_list':
          return NamespaceListResponse.fromJson(
            json
          );
                case 'interface_status':
          return InterfaceStatusResponse.fromJson(
            json
          );
                case 'interface_admit_environment_actor':
          return InterfaceAdmitEnvironmentActorResponse.fromJson(
            json
          );
                case 'interface_join_environment_session':
          return InterfaceJoinEnvironmentSessionResponse.fromJson(
            json
          );
                case 'interface_select_environment_navigation_target':
          return InterfaceSelectEnvironmentNavigationTargetResponse.fromJson(
            json
          );
                case 'interface_enter_environment':
          return InterfaceEnterEnvironmentResponse.fromJson(
            json
          );
                case 'interface_resolve_experience_lens':
          return InterfaceResolveExperienceLensResponse.fromJson(
            json
          );
                case 'interface_action':
          return InterfaceActionResponse.fromJson(
            json
          );
                case 'interface_select_step':
          return InterfaceSelectStepResponse.fromJson(
            json
          );
                case 'interface_select_profile':
          return InterfaceSelectProfileResponse.fromJson(
            json
          );
                case 'interface_select_runtime_layout':
          return InterfaceSelectRuntimeLayoutResponse.fromJson(
            json
          );
                case 'interface_activate_runtime_focus':
          return InterfaceActivateRuntimeFocusResponse.fromJson(
            json
          );
                case 'interface_request_window_layout':
          return InterfaceRequestWindowLayoutResponse.fromJson(
            json
          );
                case 'interface_apply_attention_layout_transition':
          return InterfaceApplyAttentionLayoutTransitionResponse.fromJson(
            json
          );
                case 'interface_apply_attention_layout_topology_transition':
          return InterfaceApplyAttentionLayoutTopologyTransitionResponse.fromJson(
            json
          );
                case 'interface_report_renderer_capabilities':
          return InterfaceReportRendererCapabilitiesResponse.fromJson(
            json
          );
                case 'interface_sync_view_state_cursor':
          return InterfaceSyncViewStateCursorResponse.fromJson(
            json
          );
                case 'interface_follow':
          return InterfaceFollowResponse.fromJson(
            json
          );
                case 'interface_invoke_api':
          return InterfaceInvokeApiResponse.fromJson(
            json
          );
                case 'interface_stream_api':
          return InterfaceStreamApiResponse.fromJson(
            json
          );
                case 'interface_stop':
          return InterfaceStopResponse.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'InterfaceControlPlaneResponse',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$InterfaceControlPlaneResponse {

@UuidValueConverter() UuidValue? get requestId; int get protocolVersion; bool get success; String? get error;
/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceControlPlaneResponseCopyWith<InterfaceControlPlaneResponse> get copyWith => _$InterfaceControlPlaneResponseCopyWithImpl<InterfaceControlPlaneResponse>(this as InterfaceControlPlaneResponse, _$identity);

  /// Serializes this InterfaceControlPlaneResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceControlPlaneResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error);

@override
String toString() {
  return 'InterfaceControlPlaneResponse(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error)';
}


}

/// @nodoc
abstract mixin class $InterfaceControlPlaneResponseCopyWith<$Res>  {
  factory $InterfaceControlPlaneResponseCopyWith(InterfaceControlPlaneResponse value, $Res Function(InterfaceControlPlaneResponse) _then) = _$InterfaceControlPlaneResponseCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error
});




}
/// @nodoc
class _$InterfaceControlPlaneResponseCopyWithImpl<$Res>
    implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  _$InterfaceControlPlaneResponseCopyWithImpl(this._self, this._then);

  final InterfaceControlPlaneResponse _self;
  final $Res Function(InterfaceControlPlaneResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,}) {
  return _then(_self.copyWith(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceControlPlaneResponse].
extension InterfaceControlPlaneResponsePatterns on InterfaceControlPlaneResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( PingResponse value)?  ping,TResult Function( NamespaceEnsureResponse value)?  namespaceEnsure,TResult Function( NamespaceListResponse value)?  namespaceList,TResult Function( InterfaceStatusResponse value)?  interfaceStatus,TResult Function( InterfaceAdmitEnvironmentActorResponse value)?  interfaceAdmitEnvironmentActor,TResult Function( InterfaceJoinEnvironmentSessionResponse value)?  interfaceJoinEnvironmentSession,TResult Function( InterfaceSelectEnvironmentNavigationTargetResponse value)?  interfaceSelectEnvironmentNavigationTarget,TResult Function( InterfaceEnterEnvironmentResponse value)?  interfaceEnterEnvironment,TResult Function( InterfaceResolveExperienceLensResponse value)?  interfaceResolveExperienceLens,TResult Function( InterfaceActionResponse value)?  interfaceAction,TResult Function( InterfaceSelectStepResponse value)?  interfaceSelectStep,TResult Function( InterfaceSelectProfileResponse value)?  interfaceSelectProfile,TResult Function( InterfaceSelectRuntimeLayoutResponse value)?  interfaceSelectRuntimeLayout,TResult Function( InterfaceActivateRuntimeFocusResponse value)?  interfaceActivateRuntimeFocus,TResult Function( InterfaceRequestWindowLayoutResponse value)?  interfaceRequestWindowLayout,TResult Function( InterfaceApplyAttentionLayoutTransitionResponse value)?  interfaceApplyAttentionLayoutTransition,TResult Function( InterfaceApplyAttentionLayoutTopologyTransitionResponse value)?  interfaceApplyAttentionLayoutTopologyTransition,TResult Function( InterfaceReportRendererCapabilitiesResponse value)?  interfaceReportRendererCapabilities,TResult Function( InterfaceSyncViewStateCursorResponse value)?  interfaceSyncViewStateCursor,TResult Function( InterfaceFollowResponse value)?  interfaceFollow,TResult Function( InterfaceInvokeApiResponse value)?  interfaceInvokeApi,TResult Function( InterfaceStreamApiResponse value)?  interfaceStreamApi,TResult Function( InterfaceStopResponse value)?  interfaceStop,required TResult orElse(),}){
final _that = this;
switch (_that) {
case PingResponse() when ping != null:
return ping(_that);case NamespaceEnsureResponse() when namespaceEnsure != null:
return namespaceEnsure(_that);case NamespaceListResponse() when namespaceList != null:
return namespaceList(_that);case InterfaceStatusResponse() when interfaceStatus != null:
return interfaceStatus(_that);case InterfaceAdmitEnvironmentActorResponse() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that);case InterfaceJoinEnvironmentSessionResponse() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that);case InterfaceSelectEnvironmentNavigationTargetResponse() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that);case InterfaceEnterEnvironmentResponse() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that);case InterfaceResolveExperienceLensResponse() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that);case InterfaceActionResponse() when interfaceAction != null:
return interfaceAction(_that);case InterfaceSelectStepResponse() when interfaceSelectStep != null:
return interfaceSelectStep(_that);case InterfaceSelectProfileResponse() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that);case InterfaceSelectRuntimeLayoutResponse() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that);case InterfaceActivateRuntimeFocusResponse() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that);case InterfaceRequestWindowLayoutResponse() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that);case InterfaceApplyAttentionLayoutTransitionResponse() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that);case InterfaceApplyAttentionLayoutTopologyTransitionResponse() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that);case InterfaceReportRendererCapabilitiesResponse() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that);case InterfaceSyncViewStateCursorResponse() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that);case InterfaceFollowResponse() when interfaceFollow != null:
return interfaceFollow(_that);case InterfaceInvokeApiResponse() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that);case InterfaceStreamApiResponse() when interfaceStreamApi != null:
return interfaceStreamApi(_that);case InterfaceStopResponse() when interfaceStop != null:
return interfaceStop(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( PingResponse value)  ping,required TResult Function( NamespaceEnsureResponse value)  namespaceEnsure,required TResult Function( NamespaceListResponse value)  namespaceList,required TResult Function( InterfaceStatusResponse value)  interfaceStatus,required TResult Function( InterfaceAdmitEnvironmentActorResponse value)  interfaceAdmitEnvironmentActor,required TResult Function( InterfaceJoinEnvironmentSessionResponse value)  interfaceJoinEnvironmentSession,required TResult Function( InterfaceSelectEnvironmentNavigationTargetResponse value)  interfaceSelectEnvironmentNavigationTarget,required TResult Function( InterfaceEnterEnvironmentResponse value)  interfaceEnterEnvironment,required TResult Function( InterfaceResolveExperienceLensResponse value)  interfaceResolveExperienceLens,required TResult Function( InterfaceActionResponse value)  interfaceAction,required TResult Function( InterfaceSelectStepResponse value)  interfaceSelectStep,required TResult Function( InterfaceSelectProfileResponse value)  interfaceSelectProfile,required TResult Function( InterfaceSelectRuntimeLayoutResponse value)  interfaceSelectRuntimeLayout,required TResult Function( InterfaceActivateRuntimeFocusResponse value)  interfaceActivateRuntimeFocus,required TResult Function( InterfaceRequestWindowLayoutResponse value)  interfaceRequestWindowLayout,required TResult Function( InterfaceApplyAttentionLayoutTransitionResponse value)  interfaceApplyAttentionLayoutTransition,required TResult Function( InterfaceApplyAttentionLayoutTopologyTransitionResponse value)  interfaceApplyAttentionLayoutTopologyTransition,required TResult Function( InterfaceReportRendererCapabilitiesResponse value)  interfaceReportRendererCapabilities,required TResult Function( InterfaceSyncViewStateCursorResponse value)  interfaceSyncViewStateCursor,required TResult Function( InterfaceFollowResponse value)  interfaceFollow,required TResult Function( InterfaceInvokeApiResponse value)  interfaceInvokeApi,required TResult Function( InterfaceStreamApiResponse value)  interfaceStreamApi,required TResult Function( InterfaceStopResponse value)  interfaceStop,}){
final _that = this;
switch (_that) {
case PingResponse():
return ping(_that);case NamespaceEnsureResponse():
return namespaceEnsure(_that);case NamespaceListResponse():
return namespaceList(_that);case InterfaceStatusResponse():
return interfaceStatus(_that);case InterfaceAdmitEnvironmentActorResponse():
return interfaceAdmitEnvironmentActor(_that);case InterfaceJoinEnvironmentSessionResponse():
return interfaceJoinEnvironmentSession(_that);case InterfaceSelectEnvironmentNavigationTargetResponse():
return interfaceSelectEnvironmentNavigationTarget(_that);case InterfaceEnterEnvironmentResponse():
return interfaceEnterEnvironment(_that);case InterfaceResolveExperienceLensResponse():
return interfaceResolveExperienceLens(_that);case InterfaceActionResponse():
return interfaceAction(_that);case InterfaceSelectStepResponse():
return interfaceSelectStep(_that);case InterfaceSelectProfileResponse():
return interfaceSelectProfile(_that);case InterfaceSelectRuntimeLayoutResponse():
return interfaceSelectRuntimeLayout(_that);case InterfaceActivateRuntimeFocusResponse():
return interfaceActivateRuntimeFocus(_that);case InterfaceRequestWindowLayoutResponse():
return interfaceRequestWindowLayout(_that);case InterfaceApplyAttentionLayoutTransitionResponse():
return interfaceApplyAttentionLayoutTransition(_that);case InterfaceApplyAttentionLayoutTopologyTransitionResponse():
return interfaceApplyAttentionLayoutTopologyTransition(_that);case InterfaceReportRendererCapabilitiesResponse():
return interfaceReportRendererCapabilities(_that);case InterfaceSyncViewStateCursorResponse():
return interfaceSyncViewStateCursor(_that);case InterfaceFollowResponse():
return interfaceFollow(_that);case InterfaceInvokeApiResponse():
return interfaceInvokeApi(_that);case InterfaceStreamApiResponse():
return interfaceStreamApi(_that);case InterfaceStopResponse():
return interfaceStop(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( PingResponse value)?  ping,TResult? Function( NamespaceEnsureResponse value)?  namespaceEnsure,TResult? Function( NamespaceListResponse value)?  namespaceList,TResult? Function( InterfaceStatusResponse value)?  interfaceStatus,TResult? Function( InterfaceAdmitEnvironmentActorResponse value)?  interfaceAdmitEnvironmentActor,TResult? Function( InterfaceJoinEnvironmentSessionResponse value)?  interfaceJoinEnvironmentSession,TResult? Function( InterfaceSelectEnvironmentNavigationTargetResponse value)?  interfaceSelectEnvironmentNavigationTarget,TResult? Function( InterfaceEnterEnvironmentResponse value)?  interfaceEnterEnvironment,TResult? Function( InterfaceResolveExperienceLensResponse value)?  interfaceResolveExperienceLens,TResult? Function( InterfaceActionResponse value)?  interfaceAction,TResult? Function( InterfaceSelectStepResponse value)?  interfaceSelectStep,TResult? Function( InterfaceSelectProfileResponse value)?  interfaceSelectProfile,TResult? Function( InterfaceSelectRuntimeLayoutResponse value)?  interfaceSelectRuntimeLayout,TResult? Function( InterfaceActivateRuntimeFocusResponse value)?  interfaceActivateRuntimeFocus,TResult? Function( InterfaceRequestWindowLayoutResponse value)?  interfaceRequestWindowLayout,TResult? Function( InterfaceApplyAttentionLayoutTransitionResponse value)?  interfaceApplyAttentionLayoutTransition,TResult? Function( InterfaceApplyAttentionLayoutTopologyTransitionResponse value)?  interfaceApplyAttentionLayoutTopologyTransition,TResult? Function( InterfaceReportRendererCapabilitiesResponse value)?  interfaceReportRendererCapabilities,TResult? Function( InterfaceSyncViewStateCursorResponse value)?  interfaceSyncViewStateCursor,TResult? Function( InterfaceFollowResponse value)?  interfaceFollow,TResult? Function( InterfaceInvokeApiResponse value)?  interfaceInvokeApi,TResult? Function( InterfaceStreamApiResponse value)?  interfaceStreamApi,TResult? Function( InterfaceStopResponse value)?  interfaceStop,}){
final _that = this;
switch (_that) {
case PingResponse() when ping != null:
return ping(_that);case NamespaceEnsureResponse() when namespaceEnsure != null:
return namespaceEnsure(_that);case NamespaceListResponse() when namespaceList != null:
return namespaceList(_that);case InterfaceStatusResponse() when interfaceStatus != null:
return interfaceStatus(_that);case InterfaceAdmitEnvironmentActorResponse() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that);case InterfaceJoinEnvironmentSessionResponse() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that);case InterfaceSelectEnvironmentNavigationTargetResponse() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that);case InterfaceEnterEnvironmentResponse() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that);case InterfaceResolveExperienceLensResponse() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that);case InterfaceActionResponse() when interfaceAction != null:
return interfaceAction(_that);case InterfaceSelectStepResponse() when interfaceSelectStep != null:
return interfaceSelectStep(_that);case InterfaceSelectProfileResponse() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that);case InterfaceSelectRuntimeLayoutResponse() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that);case InterfaceActivateRuntimeFocusResponse() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that);case InterfaceRequestWindowLayoutResponse() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that);case InterfaceApplyAttentionLayoutTransitionResponse() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that);case InterfaceApplyAttentionLayoutTopologyTransitionResponse() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that);case InterfaceReportRendererCapabilitiesResponse() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that);case InterfaceSyncViewStateCursorResponse() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that);case InterfaceFollowResponse() when interfaceFollow != null:
return interfaceFollow(_that);case InterfaceInvokeApiResponse() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that);case InterfaceStreamApiResponse() when interfaceStreamApi != null:
return interfaceStreamApi(_that);case InterfaceStopResponse() when interfaceStop != null:
return interfaceStop(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String service,  String status,  String? socketPath, @UuidValueConverter()  UuidValue? daemonInstanceId,  String? daemonStartedAt,  String? daemonSourceFingerprint,  String? repositoryRoot,  String? stateHome,  String? defaultEndpoint,  String? expectedSourceFingerprint,  bool restartRecommended,  String? restartReason,  List<HostedInterfaceNamespace> namespaces)?  ping,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  namespaceEnsure,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  List<HostedInterfaceNamespace> namespaces)?  namespaceList,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  interfaceStatus,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentAdmissionState? environmentAdmission,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  InterfaceHostState hostState)?  interfaceAdmitEnvironmentActor,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  EnvironmentSessionView? environmentSession,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,  InterfaceEnvironmentSessionState? environmentSessionState,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)?  interfaceJoinEnvironmentSession,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? environmentNavigationReceipt,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)?  interfaceSelectEnvironmentNavigationTarget,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentAdmissionState? environmentAdmission,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  EnvironmentSessionView? environmentSession,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,  InterfaceEnvironmentSessionState? environmentSessionState,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)?  interfaceEnterEnvironment,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentSessionState? environmentSession,  InterfaceEnvironmentNavigationState? environmentNavigation,  InterfaceExperienceLensState? experienceLens,  InterfaceHostState hostState)?  interfaceResolveExperienceLens,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String? paneRef,  String actionKey,  InterfaceHostState hostState)?  interfaceAction,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String? stepId,  InterfaceHostState hostState)?  interfaceSelectStep,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String profileId,  InterfaceHostState hostState)?  interfaceSelectProfile,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? layoutConfigId,  InterfaceHostState hostState)?  interfaceSelectRuntimeLayout,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? representationId, @UuidValueConverter()  UuidValue? layoutConfigId,  InterfaceHostState hostState)?  interfaceActivateRuntimeFocus,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName,  String? windowKey, @UuidValueConverter()  UuidValue? layoutConfigId,  String? layoutKey,  String? sectionKey, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? representationId,  String? requestedByService,  String? requestedByOperation,  String? reason,  String? idempotencyKey,  InterfaceHostState hostState)?  interfaceRequestWindowLayout,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String outcome,  String? conflictReason, @UuidValueConverter()  UuidValue? activeLayoutTransitionId, @UuidValueConverter()  UuidValue? activeTopologyTransitionId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  InterfaceHostState hostState)?  interfaceApplyAttentionLayoutTransition,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String outcome,  String? conflictReason, @UuidValueConverter()  UuidValue? activeTopologyTransitionId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  InterfaceHostState hostState)?  interfaceApplyAttentionLayoutTopologyTransition,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  interfaceReportRendererCapabilities,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  bool changed,  InterfaceHostViewStateCursorState? viewStateCursor,  InterfaceHostState hostState)?  interfaceSyncViewStateCursor,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  interfaceFollow,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String endpointRef,  String discriminant,  String? serviceStatus,  Object? responsePayload)?  interfaceInvokeApi,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String endpointRef,  String discriminant)?  interfaceStreamApi,TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  HostedInterfaceNamespace hostedNamespace)?  interfaceStop,required TResult orElse(),}) {final _that = this;
switch (_that) {
case PingResponse() when ping != null:
return ping(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.service,_that.status,_that.socketPath,_that.daemonInstanceId,_that.daemonStartedAt,_that.daemonSourceFingerprint,_that.repositoryRoot,_that.stateHome,_that.defaultEndpoint,_that.expectedSourceFingerprint,_that.restartRecommended,_that.restartReason,_that.namespaces);case NamespaceEnsureResponse() when namespaceEnsure != null:
return namespaceEnsure(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case NamespaceListResponse() when namespaceList != null:
return namespaceList(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespaces);case InterfaceStatusResponse() when interfaceStatus != null:
return interfaceStatus(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceAdmitEnvironmentActorResponse() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentAdmission,_that.environmentAdmissionReceipt,_that.hostState);case InterfaceJoinEnvironmentSessionResponse() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentSession,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.defaultNavigationReceipt,_that.environmentSessionState,_that.environmentNavigationState,_that.hostState);case InterfaceSelectEnvironmentNavigationTargetResponse() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentNavigationContext,_that.environmentNavigationReceipt,_that.environmentNavigationState,_that.hostState);case InterfaceEnterEnvironmentResponse() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentAdmission,_that.environmentAdmissionReceipt,_that.environmentSession,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.defaultNavigationReceipt,_that.environmentSessionState,_that.environmentNavigationState,_that.hostState);case InterfaceResolveExperienceLensResponse() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentSession,_that.environmentNavigation,_that.experienceLens,_that.hostState);case InterfaceActionResponse() when interfaceAction != null:
return interfaceAction(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.paneRef,_that.actionKey,_that.hostState);case InterfaceSelectStepResponse() when interfaceSelectStep != null:
return interfaceSelectStep(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.stepId,_that.hostState);case InterfaceSelectProfileResponse() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.profileId,_that.hostState);case InterfaceSelectRuntimeLayoutResponse() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.layoutConfigId,_that.hostState);case InterfaceActivateRuntimeFocusResponse() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.representationId,_that.layoutConfigId,_that.hostState);case InterfaceRequestWindowLayoutResponse() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.interfacePackageId,_that.interfacePackageName,_that.windowKey,_that.layoutConfigId,_that.layoutKey,_that.sectionKey,_that.observableId,_that.representationId,_that.requestedByService,_that.requestedByOperation,_that.reason,_that.idempotencyKey,_that.hostState);case InterfaceApplyAttentionLayoutTransitionResponse() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.outcome,_that.conflictReason,_that.activeLayoutTransitionId,_that.activeTopologyTransitionId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.hostState);case InterfaceApplyAttentionLayoutTopologyTransitionResponse() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.outcome,_that.conflictReason,_that.activeTopologyTransitionId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.hostState);case InterfaceReportRendererCapabilitiesResponse() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceSyncViewStateCursorResponse() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.changed,_that.viewStateCursor,_that.hostState);case InterfaceFollowResponse() when interfaceFollow != null:
return interfaceFollow(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceInvokeApiResponse() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.endpointRef,_that.discriminant,_that.serviceStatus,_that.responsePayload);case InterfaceStreamApiResponse() when interfaceStreamApi != null:
return interfaceStreamApi(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.endpointRef,_that.discriminant);case InterfaceStopResponse() when interfaceStop != null:
return interfaceStop(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostedNamespace);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String service,  String status,  String? socketPath, @UuidValueConverter()  UuidValue? daemonInstanceId,  String? daemonStartedAt,  String? daemonSourceFingerprint,  String? repositoryRoot,  String? stateHome,  String? defaultEndpoint,  String? expectedSourceFingerprint,  bool restartRecommended,  String? restartReason,  List<HostedInterfaceNamespace> namespaces)  ping,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)  namespaceEnsure,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  List<HostedInterfaceNamespace> namespaces)  namespaceList,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)  interfaceStatus,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentAdmissionState? environmentAdmission,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  InterfaceHostState hostState)  interfaceAdmitEnvironmentActor,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  EnvironmentSessionView? environmentSession,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,  InterfaceEnvironmentSessionState? environmentSessionState,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)  interfaceJoinEnvironmentSession,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? environmentNavigationReceipt,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)  interfaceSelectEnvironmentNavigationTarget,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentAdmissionState? environmentAdmission,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  EnvironmentSessionView? environmentSession,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,  InterfaceEnvironmentSessionState? environmentSessionState,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)  interfaceEnterEnvironment,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentSessionState? environmentSession,  InterfaceEnvironmentNavigationState? environmentNavigation,  InterfaceExperienceLensState? experienceLens,  InterfaceHostState hostState)  interfaceResolveExperienceLens,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String? paneRef,  String actionKey,  InterfaceHostState hostState)  interfaceAction,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String? stepId,  InterfaceHostState hostState)  interfaceSelectStep,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String profileId,  InterfaceHostState hostState)  interfaceSelectProfile,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? layoutConfigId,  InterfaceHostState hostState)  interfaceSelectRuntimeLayout,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? representationId, @UuidValueConverter()  UuidValue? layoutConfigId,  InterfaceHostState hostState)  interfaceActivateRuntimeFocus,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName,  String? windowKey, @UuidValueConverter()  UuidValue? layoutConfigId,  String? layoutKey,  String? sectionKey, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? representationId,  String? requestedByService,  String? requestedByOperation,  String? reason,  String? idempotencyKey,  InterfaceHostState hostState)  interfaceRequestWindowLayout,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String outcome,  String? conflictReason, @UuidValueConverter()  UuidValue? activeLayoutTransitionId, @UuidValueConverter()  UuidValue? activeTopologyTransitionId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  InterfaceHostState hostState)  interfaceApplyAttentionLayoutTransition,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String outcome,  String? conflictReason, @UuidValueConverter()  UuidValue? activeTopologyTransitionId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  InterfaceHostState hostState)  interfaceApplyAttentionLayoutTopologyTransition,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)  interfaceReportRendererCapabilities,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  bool changed,  InterfaceHostViewStateCursorState? viewStateCursor,  InterfaceHostState hostState)  interfaceSyncViewStateCursor,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)  interfaceFollow,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String endpointRef,  String discriminant,  String? serviceStatus,  Object? responsePayload)  interfaceInvokeApi,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String endpointRef,  String discriminant)  interfaceStreamApi,required TResult Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  HostedInterfaceNamespace hostedNamespace)  interfaceStop,}) {final _that = this;
switch (_that) {
case PingResponse():
return ping(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.service,_that.status,_that.socketPath,_that.daemonInstanceId,_that.daemonStartedAt,_that.daemonSourceFingerprint,_that.repositoryRoot,_that.stateHome,_that.defaultEndpoint,_that.expectedSourceFingerprint,_that.restartRecommended,_that.restartReason,_that.namespaces);case NamespaceEnsureResponse():
return namespaceEnsure(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case NamespaceListResponse():
return namespaceList(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespaces);case InterfaceStatusResponse():
return interfaceStatus(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceAdmitEnvironmentActorResponse():
return interfaceAdmitEnvironmentActor(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentAdmission,_that.environmentAdmissionReceipt,_that.hostState);case InterfaceJoinEnvironmentSessionResponse():
return interfaceJoinEnvironmentSession(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentSession,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.defaultNavigationReceipt,_that.environmentSessionState,_that.environmentNavigationState,_that.hostState);case InterfaceSelectEnvironmentNavigationTargetResponse():
return interfaceSelectEnvironmentNavigationTarget(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentNavigationContext,_that.environmentNavigationReceipt,_that.environmentNavigationState,_that.hostState);case InterfaceEnterEnvironmentResponse():
return interfaceEnterEnvironment(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentAdmission,_that.environmentAdmissionReceipt,_that.environmentSession,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.defaultNavigationReceipt,_that.environmentSessionState,_that.environmentNavigationState,_that.hostState);case InterfaceResolveExperienceLensResponse():
return interfaceResolveExperienceLens(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentSession,_that.environmentNavigation,_that.experienceLens,_that.hostState);case InterfaceActionResponse():
return interfaceAction(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.paneRef,_that.actionKey,_that.hostState);case InterfaceSelectStepResponse():
return interfaceSelectStep(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.stepId,_that.hostState);case InterfaceSelectProfileResponse():
return interfaceSelectProfile(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.profileId,_that.hostState);case InterfaceSelectRuntimeLayoutResponse():
return interfaceSelectRuntimeLayout(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.layoutConfigId,_that.hostState);case InterfaceActivateRuntimeFocusResponse():
return interfaceActivateRuntimeFocus(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.representationId,_that.layoutConfigId,_that.hostState);case InterfaceRequestWindowLayoutResponse():
return interfaceRequestWindowLayout(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.interfacePackageId,_that.interfacePackageName,_that.windowKey,_that.layoutConfigId,_that.layoutKey,_that.sectionKey,_that.observableId,_that.representationId,_that.requestedByService,_that.requestedByOperation,_that.reason,_that.idempotencyKey,_that.hostState);case InterfaceApplyAttentionLayoutTransitionResponse():
return interfaceApplyAttentionLayoutTransition(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.outcome,_that.conflictReason,_that.activeLayoutTransitionId,_that.activeTopologyTransitionId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.hostState);case InterfaceApplyAttentionLayoutTopologyTransitionResponse():
return interfaceApplyAttentionLayoutTopologyTransition(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.outcome,_that.conflictReason,_that.activeTopologyTransitionId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.hostState);case InterfaceReportRendererCapabilitiesResponse():
return interfaceReportRendererCapabilities(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceSyncViewStateCursorResponse():
return interfaceSyncViewStateCursor(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.changed,_that.viewStateCursor,_that.hostState);case InterfaceFollowResponse():
return interfaceFollow(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceInvokeApiResponse():
return interfaceInvokeApi(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.endpointRef,_that.discriminant,_that.serviceStatus,_that.responsePayload);case InterfaceStreamApiResponse():
return interfaceStreamApi(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.endpointRef,_that.discriminant);case InterfaceStopResponse():
return interfaceStop(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostedNamespace);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String service,  String status,  String? socketPath, @UuidValueConverter()  UuidValue? daemonInstanceId,  String? daemonStartedAt,  String? daemonSourceFingerprint,  String? repositoryRoot,  String? stateHome,  String? defaultEndpoint,  String? expectedSourceFingerprint,  bool restartRecommended,  String? restartReason,  List<HostedInterfaceNamespace> namespaces)?  ping,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  namespaceEnsure,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  List<HostedInterfaceNamespace> namespaces)?  namespaceList,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  interfaceStatus,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentAdmissionState? environmentAdmission,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  InterfaceHostState hostState)?  interfaceAdmitEnvironmentActor,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  EnvironmentSessionView? environmentSession,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,  InterfaceEnvironmentSessionState? environmentSessionState,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)?  interfaceJoinEnvironmentSession,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? environmentNavigationReceipt,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)?  interfaceSelectEnvironmentNavigationTarget,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentAdmissionState? environmentAdmission,  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,  EnvironmentSessionView? environmentSession,  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt,  EnvironmentNavigationContextView? environmentNavigationContext,  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt,  InterfaceEnvironmentSessionState? environmentSessionState,  InterfaceEnvironmentNavigationState? environmentNavigationState,  InterfaceHostState hostState)?  interfaceEnterEnvironment,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceEnvironmentSessionState? environmentSession,  InterfaceEnvironmentNavigationState? environmentNavigation,  InterfaceExperienceLensState? experienceLens,  InterfaceHostState hostState)?  interfaceResolveExperienceLens,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String? paneRef,  String actionKey,  InterfaceHostState hostState)?  interfaceAction,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String? stepId,  InterfaceHostState hostState)?  interfaceSelectStep,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String profileId,  InterfaceHostState hostState)?  interfaceSelectProfile,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? layoutConfigId,  InterfaceHostState hostState)?  interfaceSelectRuntimeLayout,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? representationId, @UuidValueConverter()  UuidValue? layoutConfigId,  InterfaceHostState hostState)?  interfaceActivateRuntimeFocus,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace, @UuidValueConverter()  UuidValue? interfacePackageId,  String? interfacePackageName,  String? windowKey, @UuidValueConverter()  UuidValue? layoutConfigId,  String? layoutKey,  String? sectionKey, @UuidValueConverter()  UuidValue? observableId, @UuidValueConverter()  UuidValue? representationId,  String? requestedByService,  String? requestedByOperation,  String? reason,  String? idempotencyKey,  InterfaceHostState hostState)?  interfaceRequestWindowLayout,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String outcome,  String? conflictReason, @UuidValueConverter()  UuidValue? activeLayoutTransitionId, @UuidValueConverter()  UuidValue? activeTopologyTransitionId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  InterfaceHostState hostState)?  interfaceApplyAttentionLayoutTransition,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String outcome,  String? conflictReason, @UuidValueConverter()  UuidValue? activeTopologyTransitionId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost,  InterfaceHostState hostState)?  interfaceApplyAttentionLayoutTopologyTransition,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  interfaceReportRendererCapabilities,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  bool changed,  InterfaceHostViewStateCursorState? viewStateCursor,  InterfaceHostState hostState)?  interfaceSyncViewStateCursor,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceHostState hostState)?  interfaceFollow,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String endpointRef,  String discriminant,  String? serviceStatus,  Object? responsePayload)?  interfaceInvokeApi,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  String endpointRef,  String discriminant)?  interfaceStreamApi,TResult? Function(@UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  HostedInterfaceNamespace hostedNamespace)?  interfaceStop,}) {final _that = this;
switch (_that) {
case PingResponse() when ping != null:
return ping(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.service,_that.status,_that.socketPath,_that.daemonInstanceId,_that.daemonStartedAt,_that.daemonSourceFingerprint,_that.repositoryRoot,_that.stateHome,_that.defaultEndpoint,_that.expectedSourceFingerprint,_that.restartRecommended,_that.restartReason,_that.namespaces);case NamespaceEnsureResponse() when namespaceEnsure != null:
return namespaceEnsure(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case NamespaceListResponse() when namespaceList != null:
return namespaceList(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespaces);case InterfaceStatusResponse() when interfaceStatus != null:
return interfaceStatus(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceAdmitEnvironmentActorResponse() when interfaceAdmitEnvironmentActor != null:
return interfaceAdmitEnvironmentActor(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentAdmission,_that.environmentAdmissionReceipt,_that.hostState);case InterfaceJoinEnvironmentSessionResponse() when interfaceJoinEnvironmentSession != null:
return interfaceJoinEnvironmentSession(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentSession,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.defaultNavigationReceipt,_that.environmentSessionState,_that.environmentNavigationState,_that.hostState);case InterfaceSelectEnvironmentNavigationTargetResponse() when interfaceSelectEnvironmentNavigationTarget != null:
return interfaceSelectEnvironmentNavigationTarget(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentNavigationContext,_that.environmentNavigationReceipt,_that.environmentNavigationState,_that.hostState);case InterfaceEnterEnvironmentResponse() when interfaceEnterEnvironment != null:
return interfaceEnterEnvironment(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentAdmission,_that.environmentAdmissionReceipt,_that.environmentSession,_that.environmentSessionJoinReceipt,_that.environmentNavigationContext,_that.defaultNavigationReceipt,_that.environmentSessionState,_that.environmentNavigationState,_that.hostState);case InterfaceResolveExperienceLensResponse() when interfaceResolveExperienceLens != null:
return interfaceResolveExperienceLens(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.environmentSession,_that.environmentNavigation,_that.experienceLens,_that.hostState);case InterfaceActionResponse() when interfaceAction != null:
return interfaceAction(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.paneRef,_that.actionKey,_that.hostState);case InterfaceSelectStepResponse() when interfaceSelectStep != null:
return interfaceSelectStep(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.stepId,_that.hostState);case InterfaceSelectProfileResponse() when interfaceSelectProfile != null:
return interfaceSelectProfile(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.profileId,_that.hostState);case InterfaceSelectRuntimeLayoutResponse() when interfaceSelectRuntimeLayout != null:
return interfaceSelectRuntimeLayout(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.layoutConfigId,_that.hostState);case InterfaceActivateRuntimeFocusResponse() when interfaceActivateRuntimeFocus != null:
return interfaceActivateRuntimeFocus(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.representationId,_that.layoutConfigId,_that.hostState);case InterfaceRequestWindowLayoutResponse() when interfaceRequestWindowLayout != null:
return interfaceRequestWindowLayout(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.interfacePackageId,_that.interfacePackageName,_that.windowKey,_that.layoutConfigId,_that.layoutKey,_that.sectionKey,_that.observableId,_that.representationId,_that.requestedByService,_that.requestedByOperation,_that.reason,_that.idempotencyKey,_that.hostState);case InterfaceApplyAttentionLayoutTransitionResponse() when interfaceApplyAttentionLayoutTransition != null:
return interfaceApplyAttentionLayoutTransition(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.outcome,_that.conflictReason,_that.activeLayoutTransitionId,_that.activeTopologyTransitionId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.hostState);case InterfaceApplyAttentionLayoutTopologyTransitionResponse() when interfaceApplyAttentionLayoutTopologyTransition != null:
return interfaceApplyAttentionLayoutTopologyTransition(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.outcome,_that.conflictReason,_that.activeTopologyTransitionId,_that.objectInstanceGraphCommitId,_that.graphHashPost,_that.hostState);case InterfaceReportRendererCapabilitiesResponse() when interfaceReportRendererCapabilities != null:
return interfaceReportRendererCapabilities(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceSyncViewStateCursorResponse() when interfaceSyncViewStateCursor != null:
return interfaceSyncViewStateCursor(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.changed,_that.viewStateCursor,_that.hostState);case InterfaceFollowResponse() when interfaceFollow != null:
return interfaceFollow(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostState);case InterfaceInvokeApiResponse() when interfaceInvokeApi != null:
return interfaceInvokeApi(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.endpointRef,_that.discriminant,_that.serviceStatus,_that.responsePayload);case InterfaceStreamApiResponse() when interfaceStreamApi != null:
return interfaceStreamApi(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.endpointRef,_that.discriminant);case InterfaceStopResponse() when interfaceStop != null:
return interfaceStop(_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.hostedNamespace);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class PingResponse implements InterfaceControlPlaneResponse {
   PingResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.service, required this.status, this.socketPath, @UuidValueConverter() this.daemonInstanceId, this.daemonStartedAt, this.daemonSourceFingerprint, this.repositoryRoot, this.stateHome, this.defaultEndpoint, this.expectedSourceFingerprint, required this.restartRecommended, this.restartReason, final  List<HostedInterfaceNamespace> namespaces = const [], final  String? $type}): _namespaces = namespaces,$type = $type ?? 'ping';
  factory PingResponse.fromJson(Map<String, dynamic> json) => _$PingResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String service;
 final  String status;
 final  String? socketPath;
@UuidValueConverter() final  UuidValue? daemonInstanceId;
 final  String? daemonStartedAt;
 final  String? daemonSourceFingerprint;
 final  String? repositoryRoot;
 final  String? stateHome;
 final  String? defaultEndpoint;
 final  String? expectedSourceFingerprint;
 final  bool restartRecommended;
 final  String? restartReason;
 final  List<HostedInterfaceNamespace> _namespaces;
@JsonKey() List<HostedInterfaceNamespace> get namespaces {
  if (_namespaces is EqualUnmodifiableListView) return _namespaces;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_namespaces);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$PingResponseCopyWith<PingResponse> get copyWith => _$PingResponseCopyWithImpl<PingResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$PingResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is PingResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.service, service) || other.service == service)&&(identical(other.status, status) || other.status == status)&&(identical(other.socketPath, socketPath) || other.socketPath == socketPath)&&(identical(other.daemonInstanceId, daemonInstanceId) || other.daemonInstanceId == daemonInstanceId)&&(identical(other.daemonStartedAt, daemonStartedAt) || other.daemonStartedAt == daemonStartedAt)&&(identical(other.daemonSourceFingerprint, daemonSourceFingerprint) || other.daemonSourceFingerprint == daemonSourceFingerprint)&&(identical(other.repositoryRoot, repositoryRoot) || other.repositoryRoot == repositoryRoot)&&(identical(other.stateHome, stateHome) || other.stateHome == stateHome)&&(identical(other.defaultEndpoint, defaultEndpoint) || other.defaultEndpoint == defaultEndpoint)&&(identical(other.expectedSourceFingerprint, expectedSourceFingerprint) || other.expectedSourceFingerprint == expectedSourceFingerprint)&&(identical(other.restartRecommended, restartRecommended) || other.restartRecommended == restartRecommended)&&(identical(other.restartReason, restartReason) || other.restartReason == restartReason)&&const DeepCollectionEquality().equals(other._namespaces, _namespaces));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,service,status,socketPath,daemonInstanceId,daemonStartedAt,daemonSourceFingerprint,repositoryRoot,stateHome,defaultEndpoint,expectedSourceFingerprint,restartRecommended,restartReason,const DeepCollectionEquality().hash(_namespaces));

@override
String toString() {
  return 'InterfaceControlPlaneResponse.ping(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, service: $service, status: $status, socketPath: $socketPath, daemonInstanceId: $daemonInstanceId, daemonStartedAt: $daemonStartedAt, daemonSourceFingerprint: $daemonSourceFingerprint, repositoryRoot: $repositoryRoot, stateHome: $stateHome, defaultEndpoint: $defaultEndpoint, expectedSourceFingerprint: $expectedSourceFingerprint, restartRecommended: $restartRecommended, restartReason: $restartReason, namespaces: $namespaces)';
}


}

/// @nodoc
abstract mixin class $PingResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $PingResponseCopyWith(PingResponse value, $Res Function(PingResponse) _then) = _$PingResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String service, String status, String? socketPath,@UuidValueConverter() UuidValue? daemonInstanceId, String? daemonStartedAt, String? daemonSourceFingerprint, String? repositoryRoot, String? stateHome, String? defaultEndpoint, String? expectedSourceFingerprint, bool restartRecommended, String? restartReason, List<HostedInterfaceNamespace> namespaces
});




}
/// @nodoc
class _$PingResponseCopyWithImpl<$Res>
    implements $PingResponseCopyWith<$Res> {
  _$PingResponseCopyWithImpl(this._self, this._then);

  final PingResponse _self;
  final $Res Function(PingResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? service = null,Object? status = null,Object? socketPath = freezed,Object? daemonInstanceId = freezed,Object? daemonStartedAt = freezed,Object? daemonSourceFingerprint = freezed,Object? repositoryRoot = freezed,Object? stateHome = freezed,Object? defaultEndpoint = freezed,Object? expectedSourceFingerprint = freezed,Object? restartRecommended = null,Object? restartReason = freezed,Object? namespaces = null,}) {
  return _then(PingResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,service: null == service ? _self.service : service // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,socketPath: freezed == socketPath ? _self.socketPath : socketPath // ignore: cast_nullable_to_non_nullable
as String?,daemonInstanceId: freezed == daemonInstanceId ? _self.daemonInstanceId : daemonInstanceId // ignore: cast_nullable_to_non_nullable
as UuidValue?,daemonStartedAt: freezed == daemonStartedAt ? _self.daemonStartedAt : daemonStartedAt // ignore: cast_nullable_to_non_nullable
as String?,daemonSourceFingerprint: freezed == daemonSourceFingerprint ? _self.daemonSourceFingerprint : daemonSourceFingerprint // ignore: cast_nullable_to_non_nullable
as String?,repositoryRoot: freezed == repositoryRoot ? _self.repositoryRoot : repositoryRoot // ignore: cast_nullable_to_non_nullable
as String?,stateHome: freezed == stateHome ? _self.stateHome : stateHome // ignore: cast_nullable_to_non_nullable
as String?,defaultEndpoint: freezed == defaultEndpoint ? _self.defaultEndpoint : defaultEndpoint // ignore: cast_nullable_to_non_nullable
as String?,expectedSourceFingerprint: freezed == expectedSourceFingerprint ? _self.expectedSourceFingerprint : expectedSourceFingerprint // ignore: cast_nullable_to_non_nullable
as String?,restartRecommended: null == restartRecommended ? _self.restartRecommended : restartRecommended // ignore: cast_nullable_to_non_nullable
as bool,restartReason: freezed == restartReason ? _self.restartReason : restartReason // ignore: cast_nullable_to_non_nullable
as String?,namespaces: null == namespaces ? _self._namespaces : namespaces // ignore: cast_nullable_to_non_nullable
as List<HostedInterfaceNamespace>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class NamespaceEnsureResponse implements InterfaceControlPlaneResponse {
   NamespaceEnsureResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.hostState, final  String? $type}): $type = $type ?? 'namespace_ensure';
  factory NamespaceEnsureResponse.fromJson(Map<String, dynamic> json) => _$NamespaceEnsureResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NamespaceEnsureResponseCopyWith<NamespaceEnsureResponse> get copyWith => _$NamespaceEnsureResponseCopyWithImpl<NamespaceEnsureResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NamespaceEnsureResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NamespaceEnsureResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.namespaceEnsure(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $NamespaceEnsureResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $NamespaceEnsureResponseCopyWith(NamespaceEnsureResponse value, $Res Function(NamespaceEnsureResponse) _then) = _$NamespaceEnsureResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$NamespaceEnsureResponseCopyWithImpl<$Res>
    implements $NamespaceEnsureResponseCopyWith<$Res> {
  _$NamespaceEnsureResponseCopyWithImpl(this._self, this._then);

  final NamespaceEnsureResponse _self;
  final $Res Function(NamespaceEnsureResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? hostState = null,}) {
  return _then(NamespaceEnsureResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class NamespaceListResponse implements InterfaceControlPlaneResponse {
   NamespaceListResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, final  List<HostedInterfaceNamespace> namespaces = const [], final  String? $type}): _namespaces = namespaces,$type = $type ?? 'namespace_list';
  factory NamespaceListResponse.fromJson(Map<String, dynamic> json) => _$NamespaceListResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  List<HostedInterfaceNamespace> _namespaces;
@JsonKey() List<HostedInterfaceNamespace> get namespaces {
  if (_namespaces is EqualUnmodifiableListView) return _namespaces;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_namespaces);
}


@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$NamespaceListResponseCopyWith<NamespaceListResponse> get copyWith => _$NamespaceListResponseCopyWithImpl<NamespaceListResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$NamespaceListResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is NamespaceListResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other._namespaces, _namespaces));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,const DeepCollectionEquality().hash(_namespaces));

@override
String toString() {
  return 'InterfaceControlPlaneResponse.namespaceList(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespaces: $namespaces)';
}


}

/// @nodoc
abstract mixin class $NamespaceListResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $NamespaceListResponseCopyWith(NamespaceListResponse value, $Res Function(NamespaceListResponse) _then) = _$NamespaceListResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, List<HostedInterfaceNamespace> namespaces
});




}
/// @nodoc
class _$NamespaceListResponseCopyWithImpl<$Res>
    implements $NamespaceListResponseCopyWith<$Res> {
  _$NamespaceListResponseCopyWithImpl(this._self, this._then);

  final NamespaceListResponse _self;
  final $Res Function(NamespaceListResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespaces = null,}) {
  return _then(NamespaceListResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespaces: null == namespaces ? _self._namespaces : namespaces // ignore: cast_nullable_to_non_nullable
as List<HostedInterfaceNamespace>,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceStatusResponse implements InterfaceControlPlaneResponse {
   InterfaceStatusResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.hostState, final  String? $type}): $type = $type ?? 'interface_status';
  factory InterfaceStatusResponse.fromJson(Map<String, dynamic> json) => _$InterfaceStatusResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceStatusResponseCopyWith<InterfaceStatusResponse> get copyWith => _$InterfaceStatusResponseCopyWithImpl<InterfaceStatusResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceStatusResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceStatusResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceStatus(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceStatusResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceStatusResponseCopyWith(InterfaceStatusResponse value, $Res Function(InterfaceStatusResponse) _then) = _$InterfaceStatusResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceStatusResponseCopyWithImpl<$Res>
    implements $InterfaceStatusResponseCopyWith<$Res> {
  _$InterfaceStatusResponseCopyWithImpl(this._self, this._then);

  final InterfaceStatusResponse _self;
  final $Res Function(InterfaceStatusResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? hostState = null,}) {
  return _then(InterfaceStatusResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceAdmitEnvironmentActorResponse implements InterfaceControlPlaneResponse {
   InterfaceAdmitEnvironmentActorResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.environmentAdmission, this.environmentAdmissionReceipt, required this.hostState, final  String? $type}): $type = $type ?? 'interface_admit_environment_actor';
  factory InterfaceAdmitEnvironmentActorResponse.fromJson(Map<String, dynamic> json) => _$InterfaceAdmitEnvironmentActorResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  InterfaceEnvironmentAdmissionState? environmentAdmission;
 final  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceAdmitEnvironmentActorResponseCopyWith<InterfaceAdmitEnvironmentActorResponse> get copyWith => _$InterfaceAdmitEnvironmentActorResponseCopyWithImpl<InterfaceAdmitEnvironmentActorResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceAdmitEnvironmentActorResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceAdmitEnvironmentActorResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentAdmission, environmentAdmission) || other.environmentAdmission == environmentAdmission)&&(identical(other.environmentAdmissionReceipt, environmentAdmissionReceipt) || other.environmentAdmissionReceipt == environmentAdmissionReceipt)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,environmentAdmission,environmentAdmissionReceipt,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceAdmitEnvironmentActor(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, environmentAdmission: $environmentAdmission, environmentAdmissionReceipt: $environmentAdmissionReceipt, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceAdmitEnvironmentActorResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceAdmitEnvironmentActorResponseCopyWith(InterfaceAdmitEnvironmentActorResponse value, $Res Function(InterfaceAdmitEnvironmentActorResponse) _then) = _$InterfaceAdmitEnvironmentActorResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceEnvironmentAdmissionState? environmentAdmission, EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt, InterfaceHostState hostState
});


$InterfaceEnvironmentAdmissionStateCopyWith<$Res>? get environmentAdmission;$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt;$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceAdmitEnvironmentActorResponseCopyWithImpl<$Res>
    implements $InterfaceAdmitEnvironmentActorResponseCopyWith<$Res> {
  _$InterfaceAdmitEnvironmentActorResponseCopyWithImpl(this._self, this._then);

  final InterfaceAdmitEnvironmentActorResponse _self;
  final $Res Function(InterfaceAdmitEnvironmentActorResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? environmentAdmission = freezed,Object? environmentAdmissionReceipt = freezed,Object? hostState = null,}) {
  return _then(InterfaceAdmitEnvironmentActorResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentAdmission: freezed == environmentAdmission ? _self.environmentAdmission : environmentAdmission // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentAdmissionState?,environmentAdmissionReceipt: freezed == environmentAdmissionReceipt ? _self.environmentAdmissionReceipt : environmentAdmissionReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentActorAdmissionReceipt?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentAdmissionStateCopyWith<$Res>? get environmentAdmission {
    if (_self.environmentAdmission == null) {
    return null;
  }

  return $InterfaceEnvironmentAdmissionStateCopyWith<$Res>(_self.environmentAdmission!, (value) {
    return _then(_self.copyWith(environmentAdmission: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt {
    if (_self.environmentAdmissionReceipt == null) {
    return null;
  }

  return $EnvironmentActorAdmissionReceiptCopyWith<$Res>(_self.environmentAdmissionReceipt!, (value) {
    return _then(_self.copyWith(environmentAdmissionReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceJoinEnvironmentSessionResponse implements InterfaceControlPlaneResponse {
   InterfaceJoinEnvironmentSessionResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.environmentSession, this.environmentSessionJoinReceipt, this.environmentNavigationContext, this.defaultNavigationReceipt, this.environmentSessionState, this.environmentNavigationState, required this.hostState, final  String? $type}): $type = $type ?? 'interface_join_environment_session';
  factory InterfaceJoinEnvironmentSessionResponse.fromJson(Map<String, dynamic> json) => _$InterfaceJoinEnvironmentSessionResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  EnvironmentSessionView? environmentSession;
 final  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt;
 final  EnvironmentNavigationContextView? environmentNavigationContext;
 final  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt;
 final  InterfaceEnvironmentSessionState? environmentSessionState;
 final  InterfaceEnvironmentNavigationState? environmentNavigationState;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceJoinEnvironmentSessionResponseCopyWith<InterfaceJoinEnvironmentSessionResponse> get copyWith => _$InterfaceJoinEnvironmentSessionResponseCopyWithImpl<InterfaceJoinEnvironmentSessionResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceJoinEnvironmentSessionResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceJoinEnvironmentSessionResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentSession, environmentSession) || other.environmentSession == environmentSession)&&(identical(other.environmentSessionJoinReceipt, environmentSessionJoinReceipt) || other.environmentSessionJoinReceipt == environmentSessionJoinReceipt)&&(identical(other.environmentNavigationContext, environmentNavigationContext) || other.environmentNavigationContext == environmentNavigationContext)&&(identical(other.defaultNavigationReceipt, defaultNavigationReceipt) || other.defaultNavigationReceipt == defaultNavigationReceipt)&&(identical(other.environmentSessionState, environmentSessionState) || other.environmentSessionState == environmentSessionState)&&(identical(other.environmentNavigationState, environmentNavigationState) || other.environmentNavigationState == environmentNavigationState)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,environmentSession,environmentSessionJoinReceipt,environmentNavigationContext,defaultNavigationReceipt,environmentSessionState,environmentNavigationState,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceJoinEnvironmentSession(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, environmentSession: $environmentSession, environmentSessionJoinReceipt: $environmentSessionJoinReceipt, environmentNavigationContext: $environmentNavigationContext, defaultNavigationReceipt: $defaultNavigationReceipt, environmentSessionState: $environmentSessionState, environmentNavigationState: $environmentNavigationState, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceJoinEnvironmentSessionResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceJoinEnvironmentSessionResponseCopyWith(InterfaceJoinEnvironmentSessionResponse value, $Res Function(InterfaceJoinEnvironmentSessionResponse) _then) = _$InterfaceJoinEnvironmentSessionResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, EnvironmentSessionView? environmentSession, EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt, EnvironmentNavigationContextView? environmentNavigationContext, EnvironmentNavigationCommitReceipt? defaultNavigationReceipt, InterfaceEnvironmentSessionState? environmentSessionState, InterfaceEnvironmentNavigationState? environmentNavigationState, InterfaceHostState hostState
});


$EnvironmentSessionViewCopyWith<$Res>? get environmentSession;$EnvironmentSessionJoinReceiptCopyWith<$Res>? get environmentSessionJoinReceipt;$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext;$EnvironmentNavigationCommitReceiptCopyWith<$Res>? get defaultNavigationReceipt;$InterfaceEnvironmentSessionStateCopyWith<$Res>? get environmentSessionState;$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigationState;$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceJoinEnvironmentSessionResponseCopyWithImpl<$Res>
    implements $InterfaceJoinEnvironmentSessionResponseCopyWith<$Res> {
  _$InterfaceJoinEnvironmentSessionResponseCopyWithImpl(this._self, this._then);

  final InterfaceJoinEnvironmentSessionResponse _self;
  final $Res Function(InterfaceJoinEnvironmentSessionResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? environmentSession = freezed,Object? environmentSessionJoinReceipt = freezed,Object? environmentNavigationContext = freezed,Object? defaultNavigationReceipt = freezed,Object? environmentSessionState = freezed,Object? environmentNavigationState = freezed,Object? hostState = null,}) {
  return _then(InterfaceJoinEnvironmentSessionResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentSession: freezed == environmentSession ? _self.environmentSession : environmentSession // ignore: cast_nullable_to_non_nullable
as EnvironmentSessionView?,environmentSessionJoinReceipt: freezed == environmentSessionJoinReceipt ? _self.environmentSessionJoinReceipt : environmentSessionJoinReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentSessionJoinReceipt?,environmentNavigationContext: freezed == environmentNavigationContext ? _self.environmentNavigationContext : environmentNavigationContext // ignore: cast_nullable_to_non_nullable
as EnvironmentNavigationContextView?,defaultNavigationReceipt: freezed == defaultNavigationReceipt ? _self.defaultNavigationReceipt : defaultNavigationReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentNavigationCommitReceipt?,environmentSessionState: freezed == environmentSessionState ? _self.environmentSessionState : environmentSessionState // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentSessionState?,environmentNavigationState: freezed == environmentNavigationState ? _self.environmentNavigationState : environmentNavigationState // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentNavigationState?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentSessionViewCopyWith<$Res>? get environmentSession {
    if (_self.environmentSession == null) {
    return null;
  }

  return $EnvironmentSessionViewCopyWith<$Res>(_self.environmentSession!, (value) {
    return _then(_self.copyWith(environmentSession: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentSessionJoinReceiptCopyWith<$Res>? get environmentSessionJoinReceipt {
    if (_self.environmentSessionJoinReceipt == null) {
    return null;
  }

  return $EnvironmentSessionJoinReceiptCopyWith<$Res>(_self.environmentSessionJoinReceipt!, (value) {
    return _then(_self.copyWith(environmentSessionJoinReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext {
    if (_self.environmentNavigationContext == null) {
    return null;
  }

  return $EnvironmentNavigationContextViewCopyWith<$Res>(_self.environmentNavigationContext!, (value) {
    return _then(_self.copyWith(environmentNavigationContext: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentNavigationCommitReceiptCopyWith<$Res>? get defaultNavigationReceipt {
    if (_self.defaultNavigationReceipt == null) {
    return null;
  }

  return $EnvironmentNavigationCommitReceiptCopyWith<$Res>(_self.defaultNavigationReceipt!, (value) {
    return _then(_self.copyWith(defaultNavigationReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentSessionStateCopyWith<$Res>? get environmentSessionState {
    if (_self.environmentSessionState == null) {
    return null;
  }

  return $InterfaceEnvironmentSessionStateCopyWith<$Res>(_self.environmentSessionState!, (value) {
    return _then(_self.copyWith(environmentSessionState: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigationState {
    if (_self.environmentNavigationState == null) {
    return null;
  }

  return $InterfaceEnvironmentNavigationStateCopyWith<$Res>(_self.environmentNavigationState!, (value) {
    return _then(_self.copyWith(environmentNavigationState: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectEnvironmentNavigationTargetResponse implements InterfaceControlPlaneResponse {
   InterfaceSelectEnvironmentNavigationTargetResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.environmentNavigationContext, this.environmentNavigationReceipt, this.environmentNavigationState, required this.hostState, final  String? $type}): $type = $type ?? 'interface_select_environment_navigation_target';
  factory InterfaceSelectEnvironmentNavigationTargetResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSelectEnvironmentNavigationTargetResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  EnvironmentNavigationContextView? environmentNavigationContext;
 final  EnvironmentNavigationCommitReceipt? environmentNavigationReceipt;
 final  InterfaceEnvironmentNavigationState? environmentNavigationState;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectEnvironmentNavigationTargetResponseCopyWith<InterfaceSelectEnvironmentNavigationTargetResponse> get copyWith => _$InterfaceSelectEnvironmentNavigationTargetResponseCopyWithImpl<InterfaceSelectEnvironmentNavigationTargetResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectEnvironmentNavigationTargetResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectEnvironmentNavigationTargetResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentNavigationContext, environmentNavigationContext) || other.environmentNavigationContext == environmentNavigationContext)&&(identical(other.environmentNavigationReceipt, environmentNavigationReceipt) || other.environmentNavigationReceipt == environmentNavigationReceipt)&&(identical(other.environmentNavigationState, environmentNavigationState) || other.environmentNavigationState == environmentNavigationState)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,environmentNavigationContext,environmentNavigationReceipt,environmentNavigationState,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceSelectEnvironmentNavigationTarget(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, environmentNavigationContext: $environmentNavigationContext, environmentNavigationReceipt: $environmentNavigationReceipt, environmentNavigationState: $environmentNavigationState, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectEnvironmentNavigationTargetResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceSelectEnvironmentNavigationTargetResponseCopyWith(InterfaceSelectEnvironmentNavigationTargetResponse value, $Res Function(InterfaceSelectEnvironmentNavigationTargetResponse) _then) = _$InterfaceSelectEnvironmentNavigationTargetResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, EnvironmentNavigationContextView? environmentNavigationContext, EnvironmentNavigationCommitReceipt? environmentNavigationReceipt, InterfaceEnvironmentNavigationState? environmentNavigationState, InterfaceHostState hostState
});


$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext;$EnvironmentNavigationCommitReceiptCopyWith<$Res>? get environmentNavigationReceipt;$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigationState;$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceSelectEnvironmentNavigationTargetResponseCopyWithImpl<$Res>
    implements $InterfaceSelectEnvironmentNavigationTargetResponseCopyWith<$Res> {
  _$InterfaceSelectEnvironmentNavigationTargetResponseCopyWithImpl(this._self, this._then);

  final InterfaceSelectEnvironmentNavigationTargetResponse _self;
  final $Res Function(InterfaceSelectEnvironmentNavigationTargetResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? environmentNavigationContext = freezed,Object? environmentNavigationReceipt = freezed,Object? environmentNavigationState = freezed,Object? hostState = null,}) {
  return _then(InterfaceSelectEnvironmentNavigationTargetResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentNavigationContext: freezed == environmentNavigationContext ? _self.environmentNavigationContext : environmentNavigationContext // ignore: cast_nullable_to_non_nullable
as EnvironmentNavigationContextView?,environmentNavigationReceipt: freezed == environmentNavigationReceipt ? _self.environmentNavigationReceipt : environmentNavigationReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentNavigationCommitReceipt?,environmentNavigationState: freezed == environmentNavigationState ? _self.environmentNavigationState : environmentNavigationState // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentNavigationState?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext {
    if (_self.environmentNavigationContext == null) {
    return null;
  }

  return $EnvironmentNavigationContextViewCopyWith<$Res>(_self.environmentNavigationContext!, (value) {
    return _then(_self.copyWith(environmentNavigationContext: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentNavigationCommitReceiptCopyWith<$Res>? get environmentNavigationReceipt {
    if (_self.environmentNavigationReceipt == null) {
    return null;
  }

  return $EnvironmentNavigationCommitReceiptCopyWith<$Res>(_self.environmentNavigationReceipt!, (value) {
    return _then(_self.copyWith(environmentNavigationReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigationState {
    if (_self.environmentNavigationState == null) {
    return null;
  }

  return $InterfaceEnvironmentNavigationStateCopyWith<$Res>(_self.environmentNavigationState!, (value) {
    return _then(_self.copyWith(environmentNavigationState: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceEnterEnvironmentResponse implements InterfaceControlPlaneResponse {
   InterfaceEnterEnvironmentResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.environmentAdmission, this.environmentAdmissionReceipt, this.environmentSession, this.environmentSessionJoinReceipt, this.environmentNavigationContext, this.defaultNavigationReceipt, this.environmentSessionState, this.environmentNavigationState, required this.hostState, final  String? $type}): $type = $type ?? 'interface_enter_environment';
  factory InterfaceEnterEnvironmentResponse.fromJson(Map<String, dynamic> json) => _$InterfaceEnterEnvironmentResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  InterfaceEnvironmentAdmissionState? environmentAdmission;
 final  EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt;
 final  EnvironmentSessionView? environmentSession;
 final  EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt;
 final  EnvironmentNavigationContextView? environmentNavigationContext;
 final  EnvironmentNavigationCommitReceipt? defaultNavigationReceipt;
 final  InterfaceEnvironmentSessionState? environmentSessionState;
 final  InterfaceEnvironmentNavigationState? environmentNavigationState;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceEnterEnvironmentResponseCopyWith<InterfaceEnterEnvironmentResponse> get copyWith => _$InterfaceEnterEnvironmentResponseCopyWithImpl<InterfaceEnterEnvironmentResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceEnterEnvironmentResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceEnterEnvironmentResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentAdmission, environmentAdmission) || other.environmentAdmission == environmentAdmission)&&(identical(other.environmentAdmissionReceipt, environmentAdmissionReceipt) || other.environmentAdmissionReceipt == environmentAdmissionReceipt)&&(identical(other.environmentSession, environmentSession) || other.environmentSession == environmentSession)&&(identical(other.environmentSessionJoinReceipt, environmentSessionJoinReceipt) || other.environmentSessionJoinReceipt == environmentSessionJoinReceipt)&&(identical(other.environmentNavigationContext, environmentNavigationContext) || other.environmentNavigationContext == environmentNavigationContext)&&(identical(other.defaultNavigationReceipt, defaultNavigationReceipt) || other.defaultNavigationReceipt == defaultNavigationReceipt)&&(identical(other.environmentSessionState, environmentSessionState) || other.environmentSessionState == environmentSessionState)&&(identical(other.environmentNavigationState, environmentNavigationState) || other.environmentNavigationState == environmentNavigationState)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,environmentAdmission,environmentAdmissionReceipt,environmentSession,environmentSessionJoinReceipt,environmentNavigationContext,defaultNavigationReceipt,environmentSessionState,environmentNavigationState,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceEnterEnvironment(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, environmentAdmission: $environmentAdmission, environmentAdmissionReceipt: $environmentAdmissionReceipt, environmentSession: $environmentSession, environmentSessionJoinReceipt: $environmentSessionJoinReceipt, environmentNavigationContext: $environmentNavigationContext, defaultNavigationReceipt: $defaultNavigationReceipt, environmentSessionState: $environmentSessionState, environmentNavigationState: $environmentNavigationState, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceEnterEnvironmentResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceEnterEnvironmentResponseCopyWith(InterfaceEnterEnvironmentResponse value, $Res Function(InterfaceEnterEnvironmentResponse) _then) = _$InterfaceEnterEnvironmentResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceEnvironmentAdmissionState? environmentAdmission, EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt, EnvironmentSessionView? environmentSession, EnvironmentSessionJoinReceipt? environmentSessionJoinReceipt, EnvironmentNavigationContextView? environmentNavigationContext, EnvironmentNavigationCommitReceipt? defaultNavigationReceipt, InterfaceEnvironmentSessionState? environmentSessionState, InterfaceEnvironmentNavigationState? environmentNavigationState, InterfaceHostState hostState
});


$InterfaceEnvironmentAdmissionStateCopyWith<$Res>? get environmentAdmission;$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt;$EnvironmentSessionViewCopyWith<$Res>? get environmentSession;$EnvironmentSessionJoinReceiptCopyWith<$Res>? get environmentSessionJoinReceipt;$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext;$EnvironmentNavigationCommitReceiptCopyWith<$Res>? get defaultNavigationReceipt;$InterfaceEnvironmentSessionStateCopyWith<$Res>? get environmentSessionState;$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigationState;$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceEnterEnvironmentResponseCopyWithImpl<$Res>
    implements $InterfaceEnterEnvironmentResponseCopyWith<$Res> {
  _$InterfaceEnterEnvironmentResponseCopyWithImpl(this._self, this._then);

  final InterfaceEnterEnvironmentResponse _self;
  final $Res Function(InterfaceEnterEnvironmentResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? environmentAdmission = freezed,Object? environmentAdmissionReceipt = freezed,Object? environmentSession = freezed,Object? environmentSessionJoinReceipt = freezed,Object? environmentNavigationContext = freezed,Object? defaultNavigationReceipt = freezed,Object? environmentSessionState = freezed,Object? environmentNavigationState = freezed,Object? hostState = null,}) {
  return _then(InterfaceEnterEnvironmentResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentAdmission: freezed == environmentAdmission ? _self.environmentAdmission : environmentAdmission // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentAdmissionState?,environmentAdmissionReceipt: freezed == environmentAdmissionReceipt ? _self.environmentAdmissionReceipt : environmentAdmissionReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentActorAdmissionReceipt?,environmentSession: freezed == environmentSession ? _self.environmentSession : environmentSession // ignore: cast_nullable_to_non_nullable
as EnvironmentSessionView?,environmentSessionJoinReceipt: freezed == environmentSessionJoinReceipt ? _self.environmentSessionJoinReceipt : environmentSessionJoinReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentSessionJoinReceipt?,environmentNavigationContext: freezed == environmentNavigationContext ? _self.environmentNavigationContext : environmentNavigationContext // ignore: cast_nullable_to_non_nullable
as EnvironmentNavigationContextView?,defaultNavigationReceipt: freezed == defaultNavigationReceipt ? _self.defaultNavigationReceipt : defaultNavigationReceipt // ignore: cast_nullable_to_non_nullable
as EnvironmentNavigationCommitReceipt?,environmentSessionState: freezed == environmentSessionState ? _self.environmentSessionState : environmentSessionState // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentSessionState?,environmentNavigationState: freezed == environmentNavigationState ? _self.environmentNavigationState : environmentNavigationState // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentNavigationState?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentAdmissionStateCopyWith<$Res>? get environmentAdmission {
    if (_self.environmentAdmission == null) {
    return null;
  }

  return $InterfaceEnvironmentAdmissionStateCopyWith<$Res>(_self.environmentAdmission!, (value) {
    return _then(_self.copyWith(environmentAdmission: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentActorAdmissionReceiptCopyWith<$Res>? get environmentAdmissionReceipt {
    if (_self.environmentAdmissionReceipt == null) {
    return null;
  }

  return $EnvironmentActorAdmissionReceiptCopyWith<$Res>(_self.environmentAdmissionReceipt!, (value) {
    return _then(_self.copyWith(environmentAdmissionReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentSessionViewCopyWith<$Res>? get environmentSession {
    if (_self.environmentSession == null) {
    return null;
  }

  return $EnvironmentSessionViewCopyWith<$Res>(_self.environmentSession!, (value) {
    return _then(_self.copyWith(environmentSession: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentSessionJoinReceiptCopyWith<$Res>? get environmentSessionJoinReceipt {
    if (_self.environmentSessionJoinReceipt == null) {
    return null;
  }

  return $EnvironmentSessionJoinReceiptCopyWith<$Res>(_self.environmentSessionJoinReceipt!, (value) {
    return _then(_self.copyWith(environmentSessionJoinReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentNavigationContextViewCopyWith<$Res>? get environmentNavigationContext {
    if (_self.environmentNavigationContext == null) {
    return null;
  }

  return $EnvironmentNavigationContextViewCopyWith<$Res>(_self.environmentNavigationContext!, (value) {
    return _then(_self.copyWith(environmentNavigationContext: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$EnvironmentNavigationCommitReceiptCopyWith<$Res>? get defaultNavigationReceipt {
    if (_self.defaultNavigationReceipt == null) {
    return null;
  }

  return $EnvironmentNavigationCommitReceiptCopyWith<$Res>(_self.defaultNavigationReceipt!, (value) {
    return _then(_self.copyWith(defaultNavigationReceipt: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentSessionStateCopyWith<$Res>? get environmentSessionState {
    if (_self.environmentSessionState == null) {
    return null;
  }

  return $InterfaceEnvironmentSessionStateCopyWith<$Res>(_self.environmentSessionState!, (value) {
    return _then(_self.copyWith(environmentSessionState: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigationState {
    if (_self.environmentNavigationState == null) {
    return null;
  }

  return $InterfaceEnvironmentNavigationStateCopyWith<$Res>(_self.environmentNavigationState!, (value) {
    return _then(_self.copyWith(environmentNavigationState: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceResolveExperienceLensResponse implements InterfaceControlPlaneResponse {
   InterfaceResolveExperienceLensResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.environmentSession, this.environmentNavigation, this.experienceLens, required this.hostState, final  String? $type}): $type = $type ?? 'interface_resolve_experience_lens';
  factory InterfaceResolveExperienceLensResponse.fromJson(Map<String, dynamic> json) => _$InterfaceResolveExperienceLensResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  InterfaceEnvironmentSessionState? environmentSession;
 final  InterfaceEnvironmentNavigationState? environmentNavigation;
 final  InterfaceExperienceLensState? experienceLens;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceResolveExperienceLensResponseCopyWith<InterfaceResolveExperienceLensResponse> get copyWith => _$InterfaceResolveExperienceLensResponseCopyWithImpl<InterfaceResolveExperienceLensResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceResolveExperienceLensResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceResolveExperienceLensResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.environmentSession, environmentSession) || other.environmentSession == environmentSession)&&(identical(other.environmentNavigation, environmentNavigation) || other.environmentNavigation == environmentNavigation)&&(identical(other.experienceLens, experienceLens) || other.experienceLens == experienceLens)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,environmentSession,environmentNavigation,experienceLens,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceResolveExperienceLens(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, environmentSession: $environmentSession, environmentNavigation: $environmentNavigation, experienceLens: $experienceLens, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceResolveExperienceLensResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceResolveExperienceLensResponseCopyWith(InterfaceResolveExperienceLensResponse value, $Res Function(InterfaceResolveExperienceLensResponse) _then) = _$InterfaceResolveExperienceLensResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceEnvironmentSessionState? environmentSession, InterfaceEnvironmentNavigationState? environmentNavigation, InterfaceExperienceLensState? experienceLens, InterfaceHostState hostState
});


$InterfaceEnvironmentSessionStateCopyWith<$Res>? get environmentSession;$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigation;$InterfaceExperienceLensStateCopyWith<$Res>? get experienceLens;$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceResolveExperienceLensResponseCopyWithImpl<$Res>
    implements $InterfaceResolveExperienceLensResponseCopyWith<$Res> {
  _$InterfaceResolveExperienceLensResponseCopyWithImpl(this._self, this._then);

  final InterfaceResolveExperienceLensResponse _self;
  final $Res Function(InterfaceResolveExperienceLensResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? environmentSession = freezed,Object? environmentNavigation = freezed,Object? experienceLens = freezed,Object? hostState = null,}) {
  return _then(InterfaceResolveExperienceLensResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,environmentSession: freezed == environmentSession ? _self.environmentSession : environmentSession // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentSessionState?,environmentNavigation: freezed == environmentNavigation ? _self.environmentNavigation : environmentNavigation // ignore: cast_nullable_to_non_nullable
as InterfaceEnvironmentNavigationState?,experienceLens: freezed == experienceLens ? _self.experienceLens : experienceLens // ignore: cast_nullable_to_non_nullable
as InterfaceExperienceLensState?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentSessionStateCopyWith<$Res>? get environmentSession {
    if (_self.environmentSession == null) {
    return null;
  }

  return $InterfaceEnvironmentSessionStateCopyWith<$Res>(_self.environmentSession!, (value) {
    return _then(_self.copyWith(environmentSession: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceEnvironmentNavigationStateCopyWith<$Res>? get environmentNavigation {
    if (_self.environmentNavigation == null) {
    return null;
  }

  return $InterfaceEnvironmentNavigationStateCopyWith<$Res>(_self.environmentNavigation!, (value) {
    return _then(_self.copyWith(environmentNavigation: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceExperienceLensStateCopyWith<$Res>? get experienceLens {
    if (_self.experienceLens == null) {
    return null;
  }

  return $InterfaceExperienceLensStateCopyWith<$Res>(_self.experienceLens!, (value) {
    return _then(_self.copyWith(experienceLens: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceActionResponse implements InterfaceControlPlaneResponse {
   InterfaceActionResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.paneRef, required this.actionKey, required this.hostState, final  String? $type}): $type = $type ?? 'interface_action';
  factory InterfaceActionResponse.fromJson(Map<String, dynamic> json) => _$InterfaceActionResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  String? paneRef;
 final  String actionKey;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceActionResponseCopyWith<InterfaceActionResponse> get copyWith => _$InterfaceActionResponseCopyWithImpl<InterfaceActionResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceActionResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceActionResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.paneRef, paneRef) || other.paneRef == paneRef)&&(identical(other.actionKey, actionKey) || other.actionKey == actionKey)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,paneRef,actionKey,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceAction(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, paneRef: $paneRef, actionKey: $actionKey, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceActionResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceActionResponseCopyWith(InterfaceActionResponse value, $Res Function(InterfaceActionResponse) _then) = _$InterfaceActionResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, String? paneRef, String actionKey, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceActionResponseCopyWithImpl<$Res>
    implements $InterfaceActionResponseCopyWith<$Res> {
  _$InterfaceActionResponseCopyWithImpl(this._self, this._then);

  final InterfaceActionResponse _self;
  final $Res Function(InterfaceActionResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? paneRef = freezed,Object? actionKey = null,Object? hostState = null,}) {
  return _then(InterfaceActionResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,paneRef: freezed == paneRef ? _self.paneRef : paneRef // ignore: cast_nullable_to_non_nullable
as String?,actionKey: null == actionKey ? _self.actionKey : actionKey // ignore: cast_nullable_to_non_nullable
as String,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectStepResponse implements InterfaceControlPlaneResponse {
   InterfaceSelectStepResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.stepId, required this.hostState, final  String? $type}): $type = $type ?? 'interface_select_step';
  factory InterfaceSelectStepResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSelectStepResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  String? stepId;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectStepResponseCopyWith<InterfaceSelectStepResponse> get copyWith => _$InterfaceSelectStepResponseCopyWithImpl<InterfaceSelectStepResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectStepResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectStepResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.stepId, stepId) || other.stepId == stepId)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,stepId,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceSelectStep(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, stepId: $stepId, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectStepResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceSelectStepResponseCopyWith(InterfaceSelectStepResponse value, $Res Function(InterfaceSelectStepResponse) _then) = _$InterfaceSelectStepResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, String? stepId, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceSelectStepResponseCopyWithImpl<$Res>
    implements $InterfaceSelectStepResponseCopyWith<$Res> {
  _$InterfaceSelectStepResponseCopyWithImpl(this._self, this._then);

  final InterfaceSelectStepResponse _self;
  final $Res Function(InterfaceSelectStepResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? stepId = freezed,Object? hostState = null,}) {
  return _then(InterfaceSelectStepResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,stepId: freezed == stepId ? _self.stepId : stepId // ignore: cast_nullable_to_non_nullable
as String?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectProfileResponse implements InterfaceControlPlaneResponse {
   InterfaceSelectProfileResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.profileId, required this.hostState, final  String? $type}): $type = $type ?? 'interface_select_profile';
  factory InterfaceSelectProfileResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSelectProfileResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  String profileId;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectProfileResponseCopyWith<InterfaceSelectProfileResponse> get copyWith => _$InterfaceSelectProfileResponseCopyWithImpl<InterfaceSelectProfileResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectProfileResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectProfileResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.profileId, profileId) || other.profileId == profileId)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,profileId,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceSelectProfile(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, profileId: $profileId, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectProfileResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceSelectProfileResponseCopyWith(InterfaceSelectProfileResponse value, $Res Function(InterfaceSelectProfileResponse) _then) = _$InterfaceSelectProfileResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, String profileId, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceSelectProfileResponseCopyWithImpl<$Res>
    implements $InterfaceSelectProfileResponseCopyWith<$Res> {
  _$InterfaceSelectProfileResponseCopyWithImpl(this._self, this._then);

  final InterfaceSelectProfileResponse _self;
  final $Res Function(InterfaceSelectProfileResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? profileId = null,Object? hostState = null,}) {
  return _then(InterfaceSelectProfileResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,profileId: null == profileId ? _self.profileId : profileId // ignore: cast_nullable_to_non_nullable
as String,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSelectRuntimeLayoutResponse implements InterfaceControlPlaneResponse {
   InterfaceSelectRuntimeLayoutResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, @UuidValueConverter() this.layoutConfigId, required this.hostState, final  String? $type}): $type = $type ?? 'interface_select_runtime_layout';
  factory InterfaceSelectRuntimeLayoutResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSelectRuntimeLayoutResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
@UuidValueConverter() final  UuidValue? layoutConfigId;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSelectRuntimeLayoutResponseCopyWith<InterfaceSelectRuntimeLayoutResponse> get copyWith => _$InterfaceSelectRuntimeLayoutResponseCopyWithImpl<InterfaceSelectRuntimeLayoutResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSelectRuntimeLayoutResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSelectRuntimeLayoutResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,layoutConfigId,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceSelectRuntimeLayout(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, layoutConfigId: $layoutConfigId, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceSelectRuntimeLayoutResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceSelectRuntimeLayoutResponseCopyWith(InterfaceSelectRuntimeLayoutResponse value, $Res Function(InterfaceSelectRuntimeLayoutResponse) _then) = _$InterfaceSelectRuntimeLayoutResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace,@UuidValueConverter() UuidValue? layoutConfigId, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceSelectRuntimeLayoutResponseCopyWithImpl<$Res>
    implements $InterfaceSelectRuntimeLayoutResponseCopyWith<$Res> {
  _$InterfaceSelectRuntimeLayoutResponseCopyWithImpl(this._self, this._then);

  final InterfaceSelectRuntimeLayoutResponse _self;
  final $Res Function(InterfaceSelectRuntimeLayoutResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? layoutConfigId = freezed,Object? hostState = null,}) {
  return _then(InterfaceSelectRuntimeLayoutResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,layoutConfigId: freezed == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceActivateRuntimeFocusResponse implements InterfaceControlPlaneResponse {
   InterfaceActivateRuntimeFocusResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, @UuidValueConverter() this.representationId, @UuidValueConverter() this.layoutConfigId, required this.hostState, final  String? $type}): $type = $type ?? 'interface_activate_runtime_focus';
  factory InterfaceActivateRuntimeFocusResponse.fromJson(Map<String, dynamic> json) => _$InterfaceActivateRuntimeFocusResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
@UuidValueConverter() final  UuidValue? representationId;
@UuidValueConverter() final  UuidValue? layoutConfigId;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceActivateRuntimeFocusResponseCopyWith<InterfaceActivateRuntimeFocusResponse> get copyWith => _$InterfaceActivateRuntimeFocusResponseCopyWithImpl<InterfaceActivateRuntimeFocusResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceActivateRuntimeFocusResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceActivateRuntimeFocusResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.representationId, representationId) || other.representationId == representationId)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,representationId,layoutConfigId,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceActivateRuntimeFocus(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, representationId: $representationId, layoutConfigId: $layoutConfigId, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceActivateRuntimeFocusResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceActivateRuntimeFocusResponseCopyWith(InterfaceActivateRuntimeFocusResponse value, $Res Function(InterfaceActivateRuntimeFocusResponse) _then) = _$InterfaceActivateRuntimeFocusResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace,@UuidValueConverter() UuidValue? representationId,@UuidValueConverter() UuidValue? layoutConfigId, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceActivateRuntimeFocusResponseCopyWithImpl<$Res>
    implements $InterfaceActivateRuntimeFocusResponseCopyWith<$Res> {
  _$InterfaceActivateRuntimeFocusResponseCopyWithImpl(this._self, this._then);

  final InterfaceActivateRuntimeFocusResponse _self;
  final $Res Function(InterfaceActivateRuntimeFocusResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? representationId = freezed,Object? layoutConfigId = freezed,Object? hostState = null,}) {
  return _then(InterfaceActivateRuntimeFocusResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,representationId: freezed == representationId ? _self.representationId : representationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutConfigId: freezed == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceRequestWindowLayoutResponse implements InterfaceControlPlaneResponse {
   InterfaceRequestWindowLayoutResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, @UuidValueConverter() this.interfacePackageId, this.interfacePackageName, this.windowKey, @UuidValueConverter() this.layoutConfigId, this.layoutKey, this.sectionKey, @UuidValueConverter() this.observableId, @UuidValueConverter() this.representationId, this.requestedByService, this.requestedByOperation, this.reason, this.idempotencyKey, required this.hostState, final  String? $type}): $type = $type ?? 'interface_request_window_layout';
  factory InterfaceRequestWindowLayoutResponse.fromJson(Map<String, dynamic> json) => _$InterfaceRequestWindowLayoutResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
@UuidValueConverter() final  UuidValue? interfacePackageId;
 final  String? interfacePackageName;
 final  String? windowKey;
@UuidValueConverter() final  UuidValue? layoutConfigId;
 final  String? layoutKey;
 final  String? sectionKey;
@UuidValueConverter() final  UuidValue? observableId;
@UuidValueConverter() final  UuidValue? representationId;
 final  String? requestedByService;
 final  String? requestedByOperation;
 final  String? reason;
 final  String? idempotencyKey;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceRequestWindowLayoutResponseCopyWith<InterfaceRequestWindowLayoutResponse> get copyWith => _$InterfaceRequestWindowLayoutResponseCopyWithImpl<InterfaceRequestWindowLayoutResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceRequestWindowLayoutResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceRequestWindowLayoutResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.interfacePackageId, interfacePackageId) || other.interfacePackageId == interfacePackageId)&&(identical(other.interfacePackageName, interfacePackageName) || other.interfacePackageName == interfacePackageName)&&(identical(other.windowKey, windowKey) || other.windowKey == windowKey)&&(identical(other.layoutConfigId, layoutConfigId) || other.layoutConfigId == layoutConfigId)&&(identical(other.layoutKey, layoutKey) || other.layoutKey == layoutKey)&&(identical(other.sectionKey, sectionKey) || other.sectionKey == sectionKey)&&(identical(other.observableId, observableId) || other.observableId == observableId)&&(identical(other.representationId, representationId) || other.representationId == representationId)&&(identical(other.requestedByService, requestedByService) || other.requestedByService == requestedByService)&&(identical(other.requestedByOperation, requestedByOperation) || other.requestedByOperation == requestedByOperation)&&(identical(other.reason, reason) || other.reason == reason)&&(identical(other.idempotencyKey, idempotencyKey) || other.idempotencyKey == idempotencyKey)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,interfacePackageId,interfacePackageName,windowKey,layoutConfigId,layoutKey,sectionKey,observableId,representationId,requestedByService,requestedByOperation,reason,idempotencyKey,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceRequestWindowLayout(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, interfacePackageId: $interfacePackageId, interfacePackageName: $interfacePackageName, windowKey: $windowKey, layoutConfigId: $layoutConfigId, layoutKey: $layoutKey, sectionKey: $sectionKey, observableId: $observableId, representationId: $representationId, requestedByService: $requestedByService, requestedByOperation: $requestedByOperation, reason: $reason, idempotencyKey: $idempotencyKey, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceRequestWindowLayoutResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceRequestWindowLayoutResponseCopyWith(InterfaceRequestWindowLayoutResponse value, $Res Function(InterfaceRequestWindowLayoutResponse) _then) = _$InterfaceRequestWindowLayoutResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace,@UuidValueConverter() UuidValue? interfacePackageId, String? interfacePackageName, String? windowKey,@UuidValueConverter() UuidValue? layoutConfigId, String? layoutKey, String? sectionKey,@UuidValueConverter() UuidValue? observableId,@UuidValueConverter() UuidValue? representationId, String? requestedByService, String? requestedByOperation, String? reason, String? idempotencyKey, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceRequestWindowLayoutResponseCopyWithImpl<$Res>
    implements $InterfaceRequestWindowLayoutResponseCopyWith<$Res> {
  _$InterfaceRequestWindowLayoutResponseCopyWithImpl(this._self, this._then);

  final InterfaceRequestWindowLayoutResponse _self;
  final $Res Function(InterfaceRequestWindowLayoutResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? interfacePackageId = freezed,Object? interfacePackageName = freezed,Object? windowKey = freezed,Object? layoutConfigId = freezed,Object? layoutKey = freezed,Object? sectionKey = freezed,Object? observableId = freezed,Object? representationId = freezed,Object? requestedByService = freezed,Object? requestedByOperation = freezed,Object? reason = freezed,Object? idempotencyKey = freezed,Object? hostState = null,}) {
  return _then(InterfaceRequestWindowLayoutResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,interfacePackageId: freezed == interfacePackageId ? _self.interfacePackageId : interfacePackageId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfacePackageName: freezed == interfacePackageName ? _self.interfacePackageName : interfacePackageName // ignore: cast_nullable_to_non_nullable
as String?,windowKey: freezed == windowKey ? _self.windowKey : windowKey // ignore: cast_nullable_to_non_nullable
as String?,layoutConfigId: freezed == layoutConfigId ? _self.layoutConfigId : layoutConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,layoutKey: freezed == layoutKey ? _self.layoutKey : layoutKey // ignore: cast_nullable_to_non_nullable
as String?,sectionKey: freezed == sectionKey ? _self.sectionKey : sectionKey // ignore: cast_nullable_to_non_nullable
as String?,observableId: freezed == observableId ? _self.observableId : observableId // ignore: cast_nullable_to_non_nullable
as UuidValue?,representationId: freezed == representationId ? _self.representationId : representationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestedByService: freezed == requestedByService ? _self.requestedByService : requestedByService // ignore: cast_nullable_to_non_nullable
as String?,requestedByOperation: freezed == requestedByOperation ? _self.requestedByOperation : requestedByOperation // ignore: cast_nullable_to_non_nullable
as String?,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,idempotencyKey: freezed == idempotencyKey ? _self.idempotencyKey : idempotencyKey // ignore: cast_nullable_to_non_nullable
as String?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceApplyAttentionLayoutTransitionResponse implements InterfaceControlPlaneResponse {
   InterfaceApplyAttentionLayoutTransitionResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.outcome, this.conflictReason, @UuidValueConverter() this.activeLayoutTransitionId, @UuidValueConverter() this.activeTopologyTransitionId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.graphHashPost, required this.hostState, final  String? $type}): $type = $type ?? 'interface_apply_attention_layout_transition';
  factory InterfaceApplyAttentionLayoutTransitionResponse.fromJson(Map<String, dynamic> json) => _$InterfaceApplyAttentionLayoutTransitionResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  String outcome;
 final  String? conflictReason;
@UuidValueConverter() final  UuidValue? activeLayoutTransitionId;
@UuidValueConverter() final  UuidValue? activeTopologyTransitionId;
@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
 final  String? graphHashPost;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceApplyAttentionLayoutTransitionResponseCopyWith<InterfaceApplyAttentionLayoutTransitionResponse> get copyWith => _$InterfaceApplyAttentionLayoutTransitionResponseCopyWithImpl<InterfaceApplyAttentionLayoutTransitionResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceApplyAttentionLayoutTransitionResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceApplyAttentionLayoutTransitionResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.outcome, outcome) || other.outcome == outcome)&&(identical(other.conflictReason, conflictReason) || other.conflictReason == conflictReason)&&(identical(other.activeLayoutTransitionId, activeLayoutTransitionId) || other.activeLayoutTransitionId == activeLayoutTransitionId)&&(identical(other.activeTopologyTransitionId, activeTopologyTransitionId) || other.activeTopologyTransitionId == activeTopologyTransitionId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,outcome,conflictReason,activeLayoutTransitionId,activeTopologyTransitionId,objectInstanceGraphCommitId,graphHashPost,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceApplyAttentionLayoutTransition(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, outcome: $outcome, conflictReason: $conflictReason, activeLayoutTransitionId: $activeLayoutTransitionId, activeTopologyTransitionId: $activeTopologyTransitionId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceApplyAttentionLayoutTransitionResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceApplyAttentionLayoutTransitionResponseCopyWith(InterfaceApplyAttentionLayoutTransitionResponse value, $Res Function(InterfaceApplyAttentionLayoutTransitionResponse) _then) = _$InterfaceApplyAttentionLayoutTransitionResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, String outcome, String? conflictReason,@UuidValueConverter() UuidValue? activeLayoutTransitionId,@UuidValueConverter() UuidValue? activeTopologyTransitionId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceApplyAttentionLayoutTransitionResponseCopyWithImpl<$Res>
    implements $InterfaceApplyAttentionLayoutTransitionResponseCopyWith<$Res> {
  _$InterfaceApplyAttentionLayoutTransitionResponseCopyWithImpl(this._self, this._then);

  final InterfaceApplyAttentionLayoutTransitionResponse _self;
  final $Res Function(InterfaceApplyAttentionLayoutTransitionResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? outcome = null,Object? conflictReason = freezed,Object? activeLayoutTransitionId = freezed,Object? activeTopologyTransitionId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,Object? hostState = null,}) {
  return _then(InterfaceApplyAttentionLayoutTransitionResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,outcome: null == outcome ? _self.outcome : outcome // ignore: cast_nullable_to_non_nullable
as String,conflictReason: freezed == conflictReason ? _self.conflictReason : conflictReason // ignore: cast_nullable_to_non_nullable
as String?,activeLayoutTransitionId: freezed == activeLayoutTransitionId ? _self.activeLayoutTransitionId : activeLayoutTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,activeTopologyTransitionId: freezed == activeTopologyTransitionId ? _self.activeTopologyTransitionId : activeTopologyTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceApplyAttentionLayoutTopologyTransitionResponse implements InterfaceControlPlaneResponse {
   InterfaceApplyAttentionLayoutTopologyTransitionResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.outcome, this.conflictReason, @UuidValueConverter() this.activeTopologyTransitionId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.graphHashPost, required this.hostState, final  String? $type}): $type = $type ?? 'interface_apply_attention_layout_topology_transition';
  factory InterfaceApplyAttentionLayoutTopologyTransitionResponse.fromJson(Map<String, dynamic> json) => _$InterfaceApplyAttentionLayoutTopologyTransitionResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  String outcome;
 final  String? conflictReason;
@UuidValueConverter() final  UuidValue? activeTopologyTransitionId;
@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
 final  String? graphHashPost;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWith<InterfaceApplyAttentionLayoutTopologyTransitionResponse> get copyWith => _$InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWithImpl<InterfaceApplyAttentionLayoutTopologyTransitionResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceApplyAttentionLayoutTopologyTransitionResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceApplyAttentionLayoutTopologyTransitionResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.outcome, outcome) || other.outcome == outcome)&&(identical(other.conflictReason, conflictReason) || other.conflictReason == conflictReason)&&(identical(other.activeTopologyTransitionId, activeTopologyTransitionId) || other.activeTopologyTransitionId == activeTopologyTransitionId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,outcome,conflictReason,activeTopologyTransitionId,objectInstanceGraphCommitId,graphHashPost,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceApplyAttentionLayoutTopologyTransition(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, outcome: $outcome, conflictReason: $conflictReason, activeTopologyTransitionId: $activeTopologyTransitionId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWith(InterfaceApplyAttentionLayoutTopologyTransitionResponse value, $Res Function(InterfaceApplyAttentionLayoutTopologyTransitionResponse) _then) = _$InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, String outcome, String? conflictReason,@UuidValueConverter() UuidValue? activeTopologyTransitionId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWithImpl<$Res>
    implements $InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWith<$Res> {
  _$InterfaceApplyAttentionLayoutTopologyTransitionResponseCopyWithImpl(this._self, this._then);

  final InterfaceApplyAttentionLayoutTopologyTransitionResponse _self;
  final $Res Function(InterfaceApplyAttentionLayoutTopologyTransitionResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? outcome = null,Object? conflictReason = freezed,Object? activeTopologyTransitionId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,Object? hostState = null,}) {
  return _then(InterfaceApplyAttentionLayoutTopologyTransitionResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,outcome: null == outcome ? _self.outcome : outcome // ignore: cast_nullable_to_non_nullable
as String,conflictReason: freezed == conflictReason ? _self.conflictReason : conflictReason // ignore: cast_nullable_to_non_nullable
as String?,activeTopologyTransitionId: freezed == activeTopologyTransitionId ? _self.activeTopologyTransitionId : activeTopologyTransitionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceReportRendererCapabilitiesResponse implements InterfaceControlPlaneResponse {
   InterfaceReportRendererCapabilitiesResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.hostState, final  String? $type}): $type = $type ?? 'interface_report_renderer_capabilities';
  factory InterfaceReportRendererCapabilitiesResponse.fromJson(Map<String, dynamic> json) => _$InterfaceReportRendererCapabilitiesResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceReportRendererCapabilitiesResponseCopyWith<InterfaceReportRendererCapabilitiesResponse> get copyWith => _$InterfaceReportRendererCapabilitiesResponseCopyWithImpl<InterfaceReportRendererCapabilitiesResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceReportRendererCapabilitiesResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceReportRendererCapabilitiesResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceReportRendererCapabilities(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceReportRendererCapabilitiesResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceReportRendererCapabilitiesResponseCopyWith(InterfaceReportRendererCapabilitiesResponse value, $Res Function(InterfaceReportRendererCapabilitiesResponse) _then) = _$InterfaceReportRendererCapabilitiesResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceReportRendererCapabilitiesResponseCopyWithImpl<$Res>
    implements $InterfaceReportRendererCapabilitiesResponseCopyWith<$Res> {
  _$InterfaceReportRendererCapabilitiesResponseCopyWithImpl(this._self, this._then);

  final InterfaceReportRendererCapabilitiesResponse _self;
  final $Res Function(InterfaceReportRendererCapabilitiesResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? hostState = null,}) {
  return _then(InterfaceReportRendererCapabilitiesResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceSyncViewStateCursorResponse implements InterfaceControlPlaneResponse {
   InterfaceSyncViewStateCursorResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.changed, this.viewStateCursor, required this.hostState, final  String? $type}): $type = $type ?? 'interface_sync_view_state_cursor';
  factory InterfaceSyncViewStateCursorResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSyncViewStateCursorResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  bool changed;
 final  InterfaceHostViewStateCursorState? viewStateCursor;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSyncViewStateCursorResponseCopyWith<InterfaceSyncViewStateCursorResponse> get copyWith => _$InterfaceSyncViewStateCursorResponseCopyWithImpl<InterfaceSyncViewStateCursorResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSyncViewStateCursorResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSyncViewStateCursorResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.changed, changed) || other.changed == changed)&&(identical(other.viewStateCursor, viewStateCursor) || other.viewStateCursor == viewStateCursor)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,changed,viewStateCursor,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceSyncViewStateCursor(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, changed: $changed, viewStateCursor: $viewStateCursor, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceSyncViewStateCursorResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceSyncViewStateCursorResponseCopyWith(InterfaceSyncViewStateCursorResponse value, $Res Function(InterfaceSyncViewStateCursorResponse) _then) = _$InterfaceSyncViewStateCursorResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, bool changed, InterfaceHostViewStateCursorState? viewStateCursor, InterfaceHostState hostState
});


$InterfaceHostViewStateCursorStateCopyWith<$Res>? get viewStateCursor;$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceSyncViewStateCursorResponseCopyWithImpl<$Res>
    implements $InterfaceSyncViewStateCursorResponseCopyWith<$Res> {
  _$InterfaceSyncViewStateCursorResponseCopyWithImpl(this._self, this._then);

  final InterfaceSyncViewStateCursorResponse _self;
  final $Res Function(InterfaceSyncViewStateCursorResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? changed = null,Object? viewStateCursor = freezed,Object? hostState = null,}) {
  return _then(InterfaceSyncViewStateCursorResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,changed: null == changed ? _self.changed : changed // ignore: cast_nullable_to_non_nullable
as bool,viewStateCursor: freezed == viewStateCursor ? _self.viewStateCursor : viewStateCursor // ignore: cast_nullable_to_non_nullable
as InterfaceHostViewStateCursorState?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostViewStateCursorStateCopyWith<$Res>? get viewStateCursor {
    if (_self.viewStateCursor == null) {
    return null;
  }

  return $InterfaceHostViewStateCursorStateCopyWith<$Res>(_self.viewStateCursor!, (value) {
    return _then(_self.copyWith(viewStateCursor: value));
  });
}/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceFollowResponse implements InterfaceControlPlaneResponse {
   InterfaceFollowResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.hostState, final  String? $type}): $type = $type ?? 'interface_follow';
  factory InterfaceFollowResponse.fromJson(Map<String, dynamic> json) => _$InterfaceFollowResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceFollowResponseCopyWith<InterfaceFollowResponse> get copyWith => _$InterfaceFollowResponseCopyWithImpl<InterfaceFollowResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceFollowResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceFollowResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceFollow(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceFollowResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceFollowResponseCopyWith(InterfaceFollowResponse value, $Res Function(InterfaceFollowResponse) _then) = _$InterfaceFollowResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceFollowResponseCopyWithImpl<$Res>
    implements $InterfaceFollowResponseCopyWith<$Res> {
  _$InterfaceFollowResponseCopyWithImpl(this._self, this._then);

  final InterfaceFollowResponse _self;
  final $Res Function(InterfaceFollowResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? hostState = null,}) {
  return _then(InterfaceFollowResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceInvokeApiResponse implements InterfaceControlPlaneResponse {
   InterfaceInvokeApiResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.endpointRef, required this.discriminant, this.serviceStatus, this.responsePayload, final  String? $type}): $type = $type ?? 'interface_invoke_api';
  factory InterfaceInvokeApiResponse.fromJson(Map<String, dynamic> json) => _$InterfaceInvokeApiResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  String endpointRef;
 final  String discriminant;
 final  String? serviceStatus;
 final  Object? responsePayload;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceInvokeApiResponseCopyWith<InterfaceInvokeApiResponse> get copyWith => _$InterfaceInvokeApiResponseCopyWithImpl<InterfaceInvokeApiResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceInvokeApiResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceInvokeApiResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.serviceStatus, serviceStatus) || other.serviceStatus == serviceStatus)&&const DeepCollectionEquality().equals(other.responsePayload, responsePayload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,endpointRef,discriminant,serviceStatus,const DeepCollectionEquality().hash(responsePayload));

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceInvokeApi(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, endpointRef: $endpointRef, discriminant: $discriminant, serviceStatus: $serviceStatus, responsePayload: $responsePayload)';
}


}

/// @nodoc
abstract mixin class $InterfaceInvokeApiResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceInvokeApiResponseCopyWith(InterfaceInvokeApiResponse value, $Res Function(InterfaceInvokeApiResponse) _then) = _$InterfaceInvokeApiResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, String endpointRef, String discriminant, String? serviceStatus, Object? responsePayload
});




}
/// @nodoc
class _$InterfaceInvokeApiResponseCopyWithImpl<$Res>
    implements $InterfaceInvokeApiResponseCopyWith<$Res> {
  _$InterfaceInvokeApiResponseCopyWithImpl(this._self, this._then);

  final InterfaceInvokeApiResponse _self;
  final $Res Function(InterfaceInvokeApiResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? endpointRef = null,Object? discriminant = null,Object? serviceStatus = freezed,Object? responsePayload = freezed,}) {
  return _then(InterfaceInvokeApiResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,serviceStatus: freezed == serviceStatus ? _self.serviceStatus : serviceStatus // ignore: cast_nullable_to_non_nullable
as String?,responsePayload: freezed == responsePayload ? _self.responsePayload : responsePayload ,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceStreamApiResponse implements InterfaceControlPlaneResponse {
   InterfaceStreamApiResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.endpointRef, required this.discriminant, final  String? $type}): $type = $type ?? 'interface_stream_api';
  factory InterfaceStreamApiResponse.fromJson(Map<String, dynamic> json) => _$InterfaceStreamApiResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  String endpointRef;
 final  String discriminant;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceStreamApiResponseCopyWith<InterfaceStreamApiResponse> get copyWith => _$InterfaceStreamApiResponseCopyWithImpl<InterfaceStreamApiResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceStreamApiResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceStreamApiResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,endpointRef,discriminant);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceStreamApi(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, endpointRef: $endpointRef, discriminant: $discriminant)';
}


}

/// @nodoc
abstract mixin class $InterfaceStreamApiResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceStreamApiResponseCopyWith(InterfaceStreamApiResponse value, $Res Function(InterfaceStreamApiResponse) _then) = _$InterfaceStreamApiResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, String endpointRef, String discriminant
});




}
/// @nodoc
class _$InterfaceStreamApiResponseCopyWithImpl<$Res>
    implements $InterfaceStreamApiResponseCopyWith<$Res> {
  _$InterfaceStreamApiResponseCopyWithImpl(this._self, this._then);

  final InterfaceStreamApiResponse _self;
  final $Res Function(InterfaceStreamApiResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? endpointRef = null,Object? discriminant = null,}) {
  return _then(InterfaceStreamApiResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceStopResponse implements InterfaceControlPlaneResponse {
   InterfaceStopResponse({@UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, required this.hostedNamespace, final  String? $type}): $type = $type ?? 'interface_stop';
  factory InterfaceStopResponse.fromJson(Map<String, dynamic> json) => _$InterfaceStopResponseFromJson(json);

@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
 final  String namespace;
 final  HostedInterfaceNamespace hostedNamespace;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceStopResponseCopyWith<InterfaceStopResponse> get copyWith => _$InterfaceStopResponseCopyWithImpl<InterfaceStopResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceStopResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceStopResponse&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostedNamespace, hostedNamespace) || other.hostedNamespace == hostedNamespace));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,requestId,protocolVersion,success,error,namespace,hostedNamespace);

@override
String toString() {
  return 'InterfaceControlPlaneResponse.interfaceStop(requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, hostedNamespace: $hostedNamespace)';
}


}

/// @nodoc
abstract mixin class $InterfaceStopResponseCopyWith<$Res> implements $InterfaceControlPlaneResponseCopyWith<$Res> {
  factory $InterfaceStopResponseCopyWith(InterfaceStopResponse value, $Res Function(InterfaceStopResponse) _then) = _$InterfaceStopResponseCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, HostedInterfaceNamespace hostedNamespace
});


$HostedInterfaceNamespaceCopyWith<$Res> get hostedNamespace;

}
/// @nodoc
class _$InterfaceStopResponseCopyWithImpl<$Res>
    implements $InterfaceStopResponseCopyWith<$Res> {
  _$InterfaceStopResponseCopyWithImpl(this._self, this._then);

  final InterfaceStopResponse _self;
  final $Res Function(InterfaceStopResponse) _then;

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? hostedNamespace = null,}) {
  return _then(InterfaceStopResponse(
requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostedNamespace: null == hostedNamespace ? _self.hostedNamespace : hostedNamespace // ignore: cast_nullable_to_non_nullable
as HostedInterfaceNamespace,
  ));
}

/// Create a copy of InterfaceControlPlaneResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$HostedInterfaceNamespaceCopyWith<$Res> get hostedNamespace {
  
  return $HostedInterfaceNamespaceCopyWith<$Res>(_self.hostedNamespace, (value) {
    return _then(_self.copyWith(hostedNamespace: value));
  });
}
}

InterfaceControlPlaneNotification _$InterfaceControlPlaneNotificationFromJson(
  Map<String, dynamic> json
) {
        switch (json['operation']) {
                  case 'interface_state':
          return InterfaceStateNotification.fromJson(
            json
          );
                case 'interface_api_event':
          return InterfaceApiEventNotification.fromJson(
            json
          );
                case 'interface_api_stream_closed':
          return InterfaceApiStreamClosedNotification.fromJson(
            json
          );
        
          default:
            throw CheckedFromJsonException(
  json,
  'operation',
  'InterfaceControlPlaneNotification',
  'Invalid union type "${json['operation']}"!'
);
        }
      
}

/// @nodoc
mixin _$InterfaceControlPlaneNotification {

@UuidValueConverter() UuidValue? get notificationId; int get protocolVersion; String get namespace;
/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceControlPlaneNotificationCopyWith<InterfaceControlPlaneNotification> get copyWith => _$InterfaceControlPlaneNotificationCopyWithImpl<InterfaceControlPlaneNotification>(this as InterfaceControlPlaneNotification, _$identity);

  /// Serializes this InterfaceControlPlaneNotification to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceControlPlaneNotification&&(identical(other.notificationId, notificationId) || other.notificationId == notificationId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,notificationId,protocolVersion,namespace);

@override
String toString() {
  return 'InterfaceControlPlaneNotification(notificationId: $notificationId, protocolVersion: $protocolVersion, namespace: $namespace)';
}


}

/// @nodoc
abstract mixin class $InterfaceControlPlaneNotificationCopyWith<$Res>  {
  factory $InterfaceControlPlaneNotificationCopyWith(InterfaceControlPlaneNotification value, $Res Function(InterfaceControlPlaneNotification) _then) = _$InterfaceControlPlaneNotificationCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? notificationId, int protocolVersion, String namespace
});




}
/// @nodoc
class _$InterfaceControlPlaneNotificationCopyWithImpl<$Res>
    implements $InterfaceControlPlaneNotificationCopyWith<$Res> {
  _$InterfaceControlPlaneNotificationCopyWithImpl(this._self, this._then);

  final InterfaceControlPlaneNotification _self;
  final $Res Function(InterfaceControlPlaneNotification) _then;

/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? notificationId = freezed,Object? protocolVersion = null,Object? namespace = null,}) {
  return _then(_self.copyWith(
notificationId: freezed == notificationId ? _self.notificationId : notificationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceControlPlaneNotification].
extension InterfaceControlPlaneNotificationPatterns on InterfaceControlPlaneNotification {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( InterfaceStateNotification value)?  interfaceState,TResult Function( InterfaceApiEventNotification value)?  interfaceApiEvent,TResult Function( InterfaceApiStreamClosedNotification value)?  interfaceApiStreamClosed,required TResult orElse(),}){
final _that = this;
switch (_that) {
case InterfaceStateNotification() when interfaceState != null:
return interfaceState(_that);case InterfaceApiEventNotification() when interfaceApiEvent != null:
return interfaceApiEvent(_that);case InterfaceApiStreamClosedNotification() when interfaceApiStreamClosed != null:
return interfaceApiStreamClosed(_that);case _:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( InterfaceStateNotification value)  interfaceState,required TResult Function( InterfaceApiEventNotification value)  interfaceApiEvent,required TResult Function( InterfaceApiStreamClosedNotification value)  interfaceApiStreamClosed,}){
final _that = this;
switch (_that) {
case InterfaceStateNotification():
return interfaceState(_that);case InterfaceApiEventNotification():
return interfaceApiEvent(_that);case InterfaceApiStreamClosedNotification():
return interfaceApiStreamClosed(_that);case _:
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( InterfaceStateNotification value)?  interfaceState,TResult? Function( InterfaceApiEventNotification value)?  interfaceApiEvent,TResult? Function( InterfaceApiStreamClosedNotification value)?  interfaceApiStreamClosed,}){
final _that = this;
switch (_that) {
case InterfaceStateNotification() when interfaceState != null:
return interfaceState(_that);case InterfaceApiEventNotification() when interfaceApiEvent != null:
return interfaceApiEvent(_that);case InterfaceApiStreamClosedNotification() when interfaceApiStreamClosed != null:
return interfaceApiStreamClosed(_that);case _:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  InterfaceHostState hostState)?  interfaceState,TResult Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  String eventKind,  int sequence,  String itemKey,  Object? payload)?  interfaceApiEvent,TResult Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  String? serviceStatus,  Object? responsePayload,  String? error)?  interfaceApiStreamClosed,required TResult orElse(),}) {final _that = this;
switch (_that) {
case InterfaceStateNotification() when interfaceState != null:
return interfaceState(_that.notificationId,_that.protocolVersion,_that.namespace,_that.hostState);case InterfaceApiEventNotification() when interfaceApiEvent != null:
return interfaceApiEvent(_that.notificationId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.eventKind,_that.sequence,_that.itemKey,_that.payload);case InterfaceApiStreamClosedNotification() when interfaceApiStreamClosed != null:
return interfaceApiStreamClosed(_that.notificationId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.serviceStatus,_that.responsePayload,_that.error);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  InterfaceHostState hostState)  interfaceState,required TResult Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  String eventKind,  int sequence,  String itemKey,  Object? payload)  interfaceApiEvent,required TResult Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  String? serviceStatus,  Object? responsePayload,  String? error)  interfaceApiStreamClosed,}) {final _that = this;
switch (_that) {
case InterfaceStateNotification():
return interfaceState(_that.notificationId,_that.protocolVersion,_that.namespace,_that.hostState);case InterfaceApiEventNotification():
return interfaceApiEvent(_that.notificationId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.eventKind,_that.sequence,_that.itemKey,_that.payload);case InterfaceApiStreamClosedNotification():
return interfaceApiStreamClosed(_that.notificationId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.serviceStatus,_that.responsePayload,_that.error);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  InterfaceHostState hostState)?  interfaceState,TResult? Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  String eventKind,  int sequence,  String itemKey,  Object? payload)?  interfaceApiEvent,TResult? Function(@UuidValueConverter()  UuidValue? notificationId,  int protocolVersion,  String namespace,  String endpointRef,  String discriminant,  String? serviceStatus,  Object? responsePayload,  String? error)?  interfaceApiStreamClosed,}) {final _that = this;
switch (_that) {
case InterfaceStateNotification() when interfaceState != null:
return interfaceState(_that.notificationId,_that.protocolVersion,_that.namespace,_that.hostState);case InterfaceApiEventNotification() when interfaceApiEvent != null:
return interfaceApiEvent(_that.notificationId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.eventKind,_that.sequence,_that.itemKey,_that.payload);case InterfaceApiStreamClosedNotification() when interfaceApiStreamClosed != null:
return interfaceApiStreamClosed(_that.notificationId,_that.protocolVersion,_that.namespace,_that.endpointRef,_that.discriminant,_that.serviceStatus,_that.responsePayload,_that.error);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceStateNotification implements InterfaceControlPlaneNotification {
   InterfaceStateNotification({@UuidValueConverter() this.notificationId, required this.protocolVersion, required this.namespace, required this.hostState, final  String? $type}): $type = $type ?? 'interface_state';
  factory InterfaceStateNotification.fromJson(Map<String, dynamic> json) => _$InterfaceStateNotificationFromJson(json);

@override@UuidValueConverter() final  UuidValue? notificationId;
@override final  int protocolVersion;
@override final  String namespace;
 final  InterfaceHostState hostState;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceStateNotificationCopyWith<InterfaceStateNotification> get copyWith => _$InterfaceStateNotificationCopyWithImpl<InterfaceStateNotification>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceStateNotificationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceStateNotification&&(identical(other.notificationId, notificationId) || other.notificationId == notificationId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,notificationId,protocolVersion,namespace,hostState);

@override
String toString() {
  return 'InterfaceControlPlaneNotification.interfaceState(notificationId: $notificationId, protocolVersion: $protocolVersion, namespace: $namespace, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceStateNotificationCopyWith<$Res> implements $InterfaceControlPlaneNotificationCopyWith<$Res> {
  factory $InterfaceStateNotificationCopyWith(InterfaceStateNotification value, $Res Function(InterfaceStateNotification) _then) = _$InterfaceStateNotificationCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? notificationId, int protocolVersion, String namespace, InterfaceHostState hostState
});


$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceStateNotificationCopyWithImpl<$Res>
    implements $InterfaceStateNotificationCopyWith<$Res> {
  _$InterfaceStateNotificationCopyWithImpl(this._self, this._then);

  final InterfaceStateNotification _self;
  final $Res Function(InterfaceStateNotification) _then;

/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? notificationId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? hostState = null,}) {
  return _then(InterfaceStateNotification(
notificationId: freezed == notificationId ? _self.notificationId : notificationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceApiEventNotification implements InterfaceControlPlaneNotification {
   InterfaceApiEventNotification({@UuidValueConverter() this.notificationId, required this.protocolVersion, required this.namespace, required this.endpointRef, required this.discriminant, required this.eventKind, required this.sequence, required this.itemKey, this.payload, final  String? $type}): $type = $type ?? 'interface_api_event';
  factory InterfaceApiEventNotification.fromJson(Map<String, dynamic> json) => _$InterfaceApiEventNotificationFromJson(json);

@override@UuidValueConverter() final  UuidValue? notificationId;
@override final  int protocolVersion;
@override final  String namespace;
 final  String endpointRef;
 final  String discriminant;
 final  String eventKind;
 final  int sequence;
 final  String itemKey;
 final  Object? payload;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceApiEventNotificationCopyWith<InterfaceApiEventNotification> get copyWith => _$InterfaceApiEventNotificationCopyWithImpl<InterfaceApiEventNotification>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceApiEventNotificationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceApiEventNotification&&(identical(other.notificationId, notificationId) || other.notificationId == notificationId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.eventKind, eventKind) || other.eventKind == eventKind)&&(identical(other.sequence, sequence) || other.sequence == sequence)&&(identical(other.itemKey, itemKey) || other.itemKey == itemKey)&&const DeepCollectionEquality().equals(other.payload, payload));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,notificationId,protocolVersion,namespace,endpointRef,discriminant,eventKind,sequence,itemKey,const DeepCollectionEquality().hash(payload));

@override
String toString() {
  return 'InterfaceControlPlaneNotification.interfaceApiEvent(notificationId: $notificationId, protocolVersion: $protocolVersion, namespace: $namespace, endpointRef: $endpointRef, discriminant: $discriminant, eventKind: $eventKind, sequence: $sequence, itemKey: $itemKey, payload: $payload)';
}


}

/// @nodoc
abstract mixin class $InterfaceApiEventNotificationCopyWith<$Res> implements $InterfaceControlPlaneNotificationCopyWith<$Res> {
  factory $InterfaceApiEventNotificationCopyWith(InterfaceApiEventNotification value, $Res Function(InterfaceApiEventNotification) _then) = _$InterfaceApiEventNotificationCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? notificationId, int protocolVersion, String namespace, String endpointRef, String discriminant, String eventKind, int sequence, String itemKey, Object? payload
});




}
/// @nodoc
class _$InterfaceApiEventNotificationCopyWithImpl<$Res>
    implements $InterfaceApiEventNotificationCopyWith<$Res> {
  _$InterfaceApiEventNotificationCopyWithImpl(this._self, this._then);

  final InterfaceApiEventNotification _self;
  final $Res Function(InterfaceApiEventNotification) _then;

/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? notificationId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? endpointRef = null,Object? discriminant = null,Object? eventKind = null,Object? sequence = null,Object? itemKey = null,Object? payload = freezed,}) {
  return _then(InterfaceApiEventNotification(
notificationId: freezed == notificationId ? _self.notificationId : notificationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,eventKind: null == eventKind ? _self.eventKind : eventKind // ignore: cast_nullable_to_non_nullable
as String,sequence: null == sequence ? _self.sequence : sequence // ignore: cast_nullable_to_non_nullable
as int,itemKey: null == itemKey ? _self.itemKey : itemKey // ignore: cast_nullable_to_non_nullable
as String,payload: freezed == payload ? _self.payload : payload ,
  ));
}


}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class InterfaceApiStreamClosedNotification implements InterfaceControlPlaneNotification {
   InterfaceApiStreamClosedNotification({@UuidValueConverter() this.notificationId, required this.protocolVersion, required this.namespace, required this.endpointRef, required this.discriminant, this.serviceStatus, this.responsePayload, this.error, final  String? $type}): $type = $type ?? 'interface_api_stream_closed';
  factory InterfaceApiStreamClosedNotification.fromJson(Map<String, dynamic> json) => _$InterfaceApiStreamClosedNotificationFromJson(json);

@override@UuidValueConverter() final  UuidValue? notificationId;
@override final  int protocolVersion;
@override final  String namespace;
 final  String endpointRef;
 final  String discriminant;
 final  String? serviceStatus;
 final  Object? responsePayload;
 final  String? error;

@JsonKey(name: 'operation')
final String $type;


/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceApiStreamClosedNotificationCopyWith<InterfaceApiStreamClosedNotification> get copyWith => _$InterfaceApiStreamClosedNotificationCopyWithImpl<InterfaceApiStreamClosedNotification>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceApiStreamClosedNotificationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceApiStreamClosedNotification&&(identical(other.notificationId, notificationId) || other.notificationId == notificationId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.serviceStatus, serviceStatus) || other.serviceStatus == serviceStatus)&&const DeepCollectionEquality().equals(other.responsePayload, responsePayload)&&(identical(other.error, error) || other.error == error));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,notificationId,protocolVersion,namespace,endpointRef,discriminant,serviceStatus,const DeepCollectionEquality().hash(responsePayload),error);

@override
String toString() {
  return 'InterfaceControlPlaneNotification.interfaceApiStreamClosed(notificationId: $notificationId, protocolVersion: $protocolVersion, namespace: $namespace, endpointRef: $endpointRef, discriminant: $discriminant, serviceStatus: $serviceStatus, responsePayload: $responsePayload, error: $error)';
}


}

/// @nodoc
abstract mixin class $InterfaceApiStreamClosedNotificationCopyWith<$Res> implements $InterfaceControlPlaneNotificationCopyWith<$Res> {
  factory $InterfaceApiStreamClosedNotificationCopyWith(InterfaceApiStreamClosedNotification value, $Res Function(InterfaceApiStreamClosedNotification) _then) = _$InterfaceApiStreamClosedNotificationCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? notificationId, int protocolVersion, String namespace, String endpointRef, String discriminant, String? serviceStatus, Object? responsePayload, String? error
});




}
/// @nodoc
class _$InterfaceApiStreamClosedNotificationCopyWithImpl<$Res>
    implements $InterfaceApiStreamClosedNotificationCopyWith<$Res> {
  _$InterfaceApiStreamClosedNotificationCopyWithImpl(this._self, this._then);

  final InterfaceApiStreamClosedNotification _self;
  final $Res Function(InterfaceApiStreamClosedNotification) _then;

/// Create a copy of InterfaceControlPlaneNotification
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? notificationId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? endpointRef = null,Object? discriminant = null,Object? serviceStatus = freezed,Object? responsePayload = freezed,Object? error = freezed,}) {
  return _then(InterfaceApiStreamClosedNotification(
notificationId: freezed == notificationId ? _self.notificationId : notificationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,serviceStatus: freezed == serviceStatus ? _self.serviceStatus : serviceStatus // ignore: cast_nullable_to_non_nullable
as String?,responsePayload: freezed == responsePayload ? _self.responsePayload : responsePayload ,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$InterfaceSessionStartRequest {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion;@UuidValueConverter() UuidValue get interfaceId;@UuidValueConverter() UuidValue get identitySessionId; String get name; String get state;
/// Create a copy of InterfaceSessionStartRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionStartRequestCopyWith<InterfaceSessionStartRequest> get copyWith => _$InterfaceSessionStartRequestCopyWithImpl<InterfaceSessionStartRequest>(this as InterfaceSessionStartRequest, _$identity);

  /// Serializes this InterfaceSessionStartRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionStartRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.name, name) || other.name == name)&&(identical(other.state, state) || other.state == state));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,interfaceId,identitySessionId,name,state);

@override
String toString() {
  return 'InterfaceSessionStartRequest(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, interfaceId: $interfaceId, identitySessionId: $identitySessionId, name: $name, state: $state)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionStartRequestCopyWith<$Res>  {
  factory $InterfaceSessionStartRequestCopyWith(InterfaceSessionStartRequest value, $Res Function(InterfaceSessionStartRequest) _then) = _$InterfaceSessionStartRequestCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue identitySessionId, String name, String state
});




}
/// @nodoc
class _$InterfaceSessionStartRequestCopyWithImpl<$Res>
    implements $InterfaceSessionStartRequestCopyWith<$Res> {
  _$InterfaceSessionStartRequestCopyWithImpl(this._self, this._then);

  final InterfaceSessionStartRequest _self;
  final $Res Function(InterfaceSessionStartRequest) _then;

/// Create a copy of InterfaceSessionStartRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? interfaceId = null,Object? identitySessionId = null,Object? name = null,Object? state = null,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,state: null == state ? _self.state : state // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceSessionStartRequest].
extension InterfaceSessionStartRequestPatterns on InterfaceSessionStartRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceSessionStartRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceSessionStartRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceSessionStartRequest value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionStartRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceSessionStartRequest value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionStartRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceSessionStartRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceId,_that.identitySessionId,_that.name,_that.state);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state)  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionStartRequest():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceId,_that.identitySessionId,_that.name,_that.state);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionStartRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceId,_that.identitySessionId,_that.name,_that.state);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceSessionStartRequest implements InterfaceSessionStartRequest {
   _InterfaceSessionStartRequest({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, @UuidValueConverter() required this.interfaceId, @UuidValueConverter() required this.identitySessionId, required this.name, required this.state});
  factory _InterfaceSessionStartRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSessionStartRequestFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override@UuidValueConverter() final  UuidValue interfaceId;
@override@UuidValueConverter() final  UuidValue identitySessionId;
@override final  String name;
@override final  String state;

/// Create a copy of InterfaceSessionStartRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceSessionStartRequestCopyWith<_InterfaceSessionStartRequest> get copyWith => __$InterfaceSessionStartRequestCopyWithImpl<_InterfaceSessionStartRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionStartRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceSessionStartRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.name, name) || other.name == name)&&(identical(other.state, state) || other.state == state));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,interfaceId,identitySessionId,name,state);

@override
String toString() {
  return 'InterfaceSessionStartRequest.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, interfaceId: $interfaceId, identitySessionId: $identitySessionId, name: $name, state: $state)';
}


}

/// @nodoc
abstract mixin class _$InterfaceSessionStartRequestCopyWith<$Res> implements $InterfaceSessionStartRequestCopyWith<$Res> {
  factory _$InterfaceSessionStartRequestCopyWith(_InterfaceSessionStartRequest value, $Res Function(_InterfaceSessionStartRequest) _then) = __$InterfaceSessionStartRequestCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue identitySessionId, String name, String state
});




}
/// @nodoc
class __$InterfaceSessionStartRequestCopyWithImpl<$Res>
    implements _$InterfaceSessionStartRequestCopyWith<$Res> {
  __$InterfaceSessionStartRequestCopyWithImpl(this._self, this._then);

  final _InterfaceSessionStartRequest _self;
  final $Res Function(_InterfaceSessionStartRequest) _then;

/// Create a copy of InterfaceSessionStartRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? interfaceId = null,Object? identitySessionId = null,Object? name = null,Object? state = null,}) {
  return _then(_InterfaceSessionStartRequest(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,state: null == state ? _self.state : state // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$InterfaceSessionStartResponse {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion; bool get success; String? get error;@UuidValueConverter() UuidValue? get interfaceSessionId;@UuidValueConverter() UuidValue get interfaceId;@UuidValueConverter() UuidValue get identitySessionId; String get name; String get state;@UuidValueConverter() UuidValue? get domainCommitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get graphHashPost;
/// Create a copy of InterfaceSessionStartResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionStartResponseCopyWith<InterfaceSessionStartResponse> get copyWith => _$InterfaceSessionStartResponseCopyWithImpl<InterfaceSessionStartResponse>(this as InterfaceSessionStartResponse, _$identity);

  /// Serializes this InterfaceSessionStartResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionStartResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.name, name) || other.name == name)&&(identical(other.state, state) || other.state == state)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,interfaceSessionId,interfaceId,identitySessionId,name,state,domainCommitId,objectInstanceGraphCommitId,graphHashPost);

@override
String toString() {
  return 'InterfaceSessionStartResponse(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, interfaceSessionId: $interfaceSessionId, interfaceId: $interfaceId, identitySessionId: $identitySessionId, name: $name, state: $state, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionStartResponseCopyWith<$Res>  {
  factory $InterfaceSessionStartResponseCopyWith(InterfaceSessionStartResponse value, $Res Function(InterfaceSessionStartResponse) _then) = _$InterfaceSessionStartResponseCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error,@UuidValueConverter() UuidValue? interfaceSessionId,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue identitySessionId, String name, String state,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost
});




}
/// @nodoc
class _$InterfaceSessionStartResponseCopyWithImpl<$Res>
    implements $InterfaceSessionStartResponseCopyWith<$Res> {
  _$InterfaceSessionStartResponseCopyWithImpl(this._self, this._then);

  final InterfaceSessionStartResponse _self;
  final $Res Function(InterfaceSessionStartResponse) _then;

/// Create a copy of InterfaceSessionStartResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? interfaceSessionId = freezed,Object? interfaceId = null,Object? identitySessionId = null,Object? name = null,Object? state = null,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,interfaceSessionId: freezed == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,state: null == state ? _self.state : state // ignore: cast_nullable_to_non_nullable
as String,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceSessionStartResponse].
extension InterfaceSessionStartResponsePatterns on InterfaceSessionStartResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceSessionStartResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceSessionStartResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceSessionStartResponse value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionStartResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceSessionStartResponse value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionStartResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceSessionStartResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.interfaceSessionId,_that.interfaceId,_that.identitySessionId,_that.name,_that.state,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.graphHashPost);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost)  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionStartResponse():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.interfaceSessionId,_that.interfaceId,_that.identitySessionId,_that.name,_that.state,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.graphHashPost);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error, @UuidValueConverter()  UuidValue? interfaceSessionId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionStartResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.interfaceSessionId,_that.interfaceId,_that.identitySessionId,_that.name,_that.state,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.graphHashPost);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceSessionStartResponse implements InterfaceSessionStartResponse {
   _InterfaceSessionStartResponse({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, @UuidValueConverter() this.interfaceSessionId, @UuidValueConverter() required this.interfaceId, @UuidValueConverter() required this.identitySessionId, required this.name, required this.state, @UuidValueConverter() this.domainCommitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.graphHashPost});
  factory _InterfaceSessionStartResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSessionStartResponseFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
@override@UuidValueConverter() final  UuidValue? interfaceSessionId;
@override@UuidValueConverter() final  UuidValue interfaceId;
@override@UuidValueConverter() final  UuidValue identitySessionId;
@override final  String name;
@override final  String state;
@override@UuidValueConverter() final  UuidValue? domainCommitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? graphHashPost;

/// Create a copy of InterfaceSessionStartResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceSessionStartResponseCopyWith<_InterfaceSessionStartResponse> get copyWith => __$InterfaceSessionStartResponseCopyWithImpl<_InterfaceSessionStartResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionStartResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceSessionStartResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.name, name) || other.name == name)&&(identical(other.state, state) || other.state == state)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,interfaceSessionId,interfaceId,identitySessionId,name,state,domainCommitId,objectInstanceGraphCommitId,graphHashPost);

@override
String toString() {
  return 'InterfaceSessionStartResponse.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, interfaceSessionId: $interfaceSessionId, interfaceId: $interfaceId, identitySessionId: $identitySessionId, name: $name, state: $state, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost)';
}


}

/// @nodoc
abstract mixin class _$InterfaceSessionStartResponseCopyWith<$Res> implements $InterfaceSessionStartResponseCopyWith<$Res> {
  factory _$InterfaceSessionStartResponseCopyWith(_InterfaceSessionStartResponse value, $Res Function(_InterfaceSessionStartResponse) _then) = __$InterfaceSessionStartResponseCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error,@UuidValueConverter() UuidValue? interfaceSessionId,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue identitySessionId, String name, String state,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost
});




}
/// @nodoc
class __$InterfaceSessionStartResponseCopyWithImpl<$Res>
    implements _$InterfaceSessionStartResponseCopyWith<$Res> {
  __$InterfaceSessionStartResponseCopyWithImpl(this._self, this._then);

  final _InterfaceSessionStartResponse _self;
  final $Res Function(_InterfaceSessionStartResponse) _then;

/// Create a copy of InterfaceSessionStartResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? interfaceSessionId = freezed,Object? interfaceId = null,Object? identitySessionId = null,Object? name = null,Object? state = null,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,}) {
  return _then(_InterfaceSessionStartResponse(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,interfaceSessionId: freezed == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,state: null == state ? _self.state : state // ignore: cast_nullable_to_non_nullable
as String,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$InterfaceSessionDescribeRequest {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion;@UuidValueConverter() UuidValue get interfaceSessionId;
/// Create a copy of InterfaceSessionDescribeRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionDescribeRequestCopyWith<InterfaceSessionDescribeRequest> get copyWith => _$InterfaceSessionDescribeRequestCopyWithImpl<InterfaceSessionDescribeRequest>(this as InterfaceSessionDescribeRequest, _$identity);

  /// Serializes this InterfaceSessionDescribeRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionDescribeRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,interfaceSessionId);

@override
String toString() {
  return 'InterfaceSessionDescribeRequest(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, interfaceSessionId: $interfaceSessionId)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionDescribeRequestCopyWith<$Res>  {
  factory $InterfaceSessionDescribeRequestCopyWith(InterfaceSessionDescribeRequest value, $Res Function(InterfaceSessionDescribeRequest) _then) = _$InterfaceSessionDescribeRequestCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion,@UuidValueConverter() UuidValue interfaceSessionId
});




}
/// @nodoc
class _$InterfaceSessionDescribeRequestCopyWithImpl<$Res>
    implements $InterfaceSessionDescribeRequestCopyWith<$Res> {
  _$InterfaceSessionDescribeRequestCopyWithImpl(this._self, this._then);

  final InterfaceSessionDescribeRequest _self;
  final $Res Function(InterfaceSessionDescribeRequest) _then;

/// Create a copy of InterfaceSessionDescribeRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? interfaceSessionId = null,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceSessionDescribeRequest].
extension InterfaceSessionDescribeRequestPatterns on InterfaceSessionDescribeRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceSessionDescribeRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceSessionDescribeRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceSessionDescribeRequest value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionDescribeRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceSessionDescribeRequest value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionDescribeRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceSessionId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceSessionDescribeRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceSessionId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceSessionId)  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionDescribeRequest():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceSessionId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceSessionId)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionDescribeRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceSessionId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceSessionDescribeRequest implements InterfaceSessionDescribeRequest {
   _InterfaceSessionDescribeRequest({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, @UuidValueConverter() required this.interfaceSessionId});
  factory _InterfaceSessionDescribeRequest.fromJson(Map<String, dynamic> json) => _$InterfaceSessionDescribeRequestFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override@UuidValueConverter() final  UuidValue interfaceSessionId;

/// Create a copy of InterfaceSessionDescribeRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceSessionDescribeRequestCopyWith<_InterfaceSessionDescribeRequest> get copyWith => __$InterfaceSessionDescribeRequestCopyWithImpl<_InterfaceSessionDescribeRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionDescribeRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceSessionDescribeRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,interfaceSessionId);

@override
String toString() {
  return 'InterfaceSessionDescribeRequest.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, interfaceSessionId: $interfaceSessionId)';
}


}

/// @nodoc
abstract mixin class _$InterfaceSessionDescribeRequestCopyWith<$Res> implements $InterfaceSessionDescribeRequestCopyWith<$Res> {
  factory _$InterfaceSessionDescribeRequestCopyWith(_InterfaceSessionDescribeRequest value, $Res Function(_InterfaceSessionDescribeRequest) _then) = __$InterfaceSessionDescribeRequestCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion,@UuidValueConverter() UuidValue interfaceSessionId
});




}
/// @nodoc
class __$InterfaceSessionDescribeRequestCopyWithImpl<$Res>
    implements _$InterfaceSessionDescribeRequestCopyWith<$Res> {
  __$InterfaceSessionDescribeRequestCopyWithImpl(this._self, this._then);

  final _InterfaceSessionDescribeRequest _self;
  final $Res Function(_InterfaceSessionDescribeRequest) _then;

/// Create a copy of InterfaceSessionDescribeRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? interfaceSessionId = null,}) {
  return _then(_InterfaceSessionDescribeRequest(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}


/// @nodoc
mixin _$InterfaceSessionExperienceSessionView {

@UuidValueConverter() UuidValue get interfaceSessionExperienceSessionId;@UuidValueConverter() UuidValue get experienceSessionId; String get status; Map<String, dynamic>? get metadataJson;@UuidValueConverter() UuidValue get domainCommitId;
/// Create a copy of InterfaceSessionExperienceSessionView
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionExperienceSessionViewCopyWith<InterfaceSessionExperienceSessionView> get copyWith => _$InterfaceSessionExperienceSessionViewCopyWithImpl<InterfaceSessionExperienceSessionView>(this as InterfaceSessionExperienceSessionView, _$identity);

  /// Serializes this InterfaceSessionExperienceSessionView to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionExperienceSessionView&&(identical(other.interfaceSessionExperienceSessionId, interfaceSessionExperienceSessionId) || other.interfaceSessionExperienceSessionId == interfaceSessionExperienceSessionId)&&(identical(other.experienceSessionId, experienceSessionId) || other.experienceSessionId == experienceSessionId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceSessionExperienceSessionId,experienceSessionId,status,const DeepCollectionEquality().hash(metadataJson),domainCommitId);

@override
String toString() {
  return 'InterfaceSessionExperienceSessionView(interfaceSessionExperienceSessionId: $interfaceSessionExperienceSessionId, experienceSessionId: $experienceSessionId, status: $status, metadataJson: $metadataJson, domainCommitId: $domainCommitId)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionExperienceSessionViewCopyWith<$Res>  {
  factory $InterfaceSessionExperienceSessionViewCopyWith(InterfaceSessionExperienceSessionView value, $Res Function(InterfaceSessionExperienceSessionView) _then) = _$InterfaceSessionExperienceSessionViewCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue interfaceSessionExperienceSessionId,@UuidValueConverter() UuidValue experienceSessionId, String status, Map<String, dynamic>? metadataJson,@UuidValueConverter() UuidValue domainCommitId
});




}
/// @nodoc
class _$InterfaceSessionExperienceSessionViewCopyWithImpl<$Res>
    implements $InterfaceSessionExperienceSessionViewCopyWith<$Res> {
  _$InterfaceSessionExperienceSessionViewCopyWithImpl(this._self, this._then);

  final InterfaceSessionExperienceSessionView _self;
  final $Res Function(InterfaceSessionExperienceSessionView) _then;

/// Create a copy of InterfaceSessionExperienceSessionView
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? interfaceSessionExperienceSessionId = null,Object? experienceSessionId = null,Object? status = null,Object? metadataJson = freezed,Object? domainCommitId = null,}) {
  return _then(_self.copyWith(
interfaceSessionExperienceSessionId: null == interfaceSessionExperienceSessionId ? _self.interfaceSessionExperienceSessionId : interfaceSessionExperienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessionId: null == experienceSessionId ? _self.experienceSessionId : experienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: freezed == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,domainCommitId: null == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceSessionExperienceSessionView].
extension InterfaceSessionExperienceSessionViewPatterns on InterfaceSessionExperienceSessionView {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceSessionExperienceSessionView value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceSessionExperienceSessionView() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceSessionExperienceSessionView value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionExperienceSessionView():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceSessionExperienceSessionView value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionExperienceSessionView() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue interfaceSessionExperienceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson, @UuidValueConverter()  UuidValue domainCommitId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceSessionExperienceSessionView() when def != null:
return def(_that.interfaceSessionExperienceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson,_that.domainCommitId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue interfaceSessionExperienceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson, @UuidValueConverter()  UuidValue domainCommitId)  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionExperienceSessionView():
return def(_that.interfaceSessionExperienceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson,_that.domainCommitId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue interfaceSessionExperienceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson, @UuidValueConverter()  UuidValue domainCommitId)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionExperienceSessionView() when def != null:
return def(_that.interfaceSessionExperienceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson,_that.domainCommitId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceSessionExperienceSessionView implements InterfaceSessionExperienceSessionView {
   _InterfaceSessionExperienceSessionView({@UuidValueConverter() required this.interfaceSessionExperienceSessionId, @UuidValueConverter() required this.experienceSessionId, required this.status, final  Map<String, dynamic>? metadataJson, @UuidValueConverter() required this.domainCommitId}): _metadataJson = metadataJson;
  factory _InterfaceSessionExperienceSessionView.fromJson(Map<String, dynamic> json) => _$InterfaceSessionExperienceSessionViewFromJson(json);

@override@UuidValueConverter() final  UuidValue interfaceSessionExperienceSessionId;
@override@UuidValueConverter() final  UuidValue experienceSessionId;
@override final  String status;
 final  Map<String, dynamic>? _metadataJson;
@override Map<String, dynamic>? get metadataJson {
  final value = _metadataJson;
  if (value == null) return null;
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(value);
}

@override@UuidValueConverter() final  UuidValue domainCommitId;

/// Create a copy of InterfaceSessionExperienceSessionView
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceSessionExperienceSessionViewCopyWith<_InterfaceSessionExperienceSessionView> get copyWith => __$InterfaceSessionExperienceSessionViewCopyWithImpl<_InterfaceSessionExperienceSessionView>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionExperienceSessionViewToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceSessionExperienceSessionView&&(identical(other.interfaceSessionExperienceSessionId, interfaceSessionExperienceSessionId) || other.interfaceSessionExperienceSessionId == interfaceSessionExperienceSessionId)&&(identical(other.experienceSessionId, experienceSessionId) || other.experienceSessionId == experienceSessionId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceSessionExperienceSessionId,experienceSessionId,status,const DeepCollectionEquality().hash(_metadataJson),domainCommitId);

@override
String toString() {
  return 'InterfaceSessionExperienceSessionView.def(interfaceSessionExperienceSessionId: $interfaceSessionExperienceSessionId, experienceSessionId: $experienceSessionId, status: $status, metadataJson: $metadataJson, domainCommitId: $domainCommitId)';
}


}

/// @nodoc
abstract mixin class _$InterfaceSessionExperienceSessionViewCopyWith<$Res> implements $InterfaceSessionExperienceSessionViewCopyWith<$Res> {
  factory _$InterfaceSessionExperienceSessionViewCopyWith(_InterfaceSessionExperienceSessionView value, $Res Function(_InterfaceSessionExperienceSessionView) _then) = __$InterfaceSessionExperienceSessionViewCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue interfaceSessionExperienceSessionId,@UuidValueConverter() UuidValue experienceSessionId, String status, Map<String, dynamic>? metadataJson,@UuidValueConverter() UuidValue domainCommitId
});




}
/// @nodoc
class __$InterfaceSessionExperienceSessionViewCopyWithImpl<$Res>
    implements _$InterfaceSessionExperienceSessionViewCopyWith<$Res> {
  __$InterfaceSessionExperienceSessionViewCopyWithImpl(this._self, this._then);

  final _InterfaceSessionExperienceSessionView _self;
  final $Res Function(_InterfaceSessionExperienceSessionView) _then;

/// Create a copy of InterfaceSessionExperienceSessionView
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? interfaceSessionExperienceSessionId = null,Object? experienceSessionId = null,Object? status = null,Object? metadataJson = freezed,Object? domainCommitId = null,}) {
  return _then(_InterfaceSessionExperienceSessionView(
interfaceSessionExperienceSessionId: null == interfaceSessionExperienceSessionId ? _self.interfaceSessionExperienceSessionId : interfaceSessionExperienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessionId: null == experienceSessionId ? _self.experienceSessionId : experienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: freezed == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,domainCommitId: null == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,
  ));
}


}


/// @nodoc
mixin _$InterfaceSessionView {

@UuidValueConverter() UuidValue get interfaceSessionId;@UuidValueConverter() UuidValue get interfaceId;@UuidValueConverter() UuidValue get identitySessionId; String get name; String get state;@UuidValueConverter() UuidValue get domainCommitId; List<InterfaceSessionExperienceSessionView> get experienceSessions;
/// Create a copy of InterfaceSessionView
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionViewCopyWith<InterfaceSessionView> get copyWith => _$InterfaceSessionViewCopyWithImpl<InterfaceSessionView>(this as InterfaceSessionView, _$identity);

  /// Serializes this InterfaceSessionView to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionView&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.name, name) || other.name == name)&&(identical(other.state, state) || other.state == state)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&const DeepCollectionEquality().equals(other.experienceSessions, experienceSessions));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceSessionId,interfaceId,identitySessionId,name,state,domainCommitId,const DeepCollectionEquality().hash(experienceSessions));

@override
String toString() {
  return 'InterfaceSessionView(interfaceSessionId: $interfaceSessionId, interfaceId: $interfaceId, identitySessionId: $identitySessionId, name: $name, state: $state, domainCommitId: $domainCommitId, experienceSessions: $experienceSessions)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionViewCopyWith<$Res>  {
  factory $InterfaceSessionViewCopyWith(InterfaceSessionView value, $Res Function(InterfaceSessionView) _then) = _$InterfaceSessionViewCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue interfaceSessionId,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue identitySessionId, String name, String state,@UuidValueConverter() UuidValue domainCommitId, List<InterfaceSessionExperienceSessionView> experienceSessions
});




}
/// @nodoc
class _$InterfaceSessionViewCopyWithImpl<$Res>
    implements $InterfaceSessionViewCopyWith<$Res> {
  _$InterfaceSessionViewCopyWithImpl(this._self, this._then);

  final InterfaceSessionView _self;
  final $Res Function(InterfaceSessionView) _then;

/// Create a copy of InterfaceSessionView
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? interfaceSessionId = null,Object? interfaceId = null,Object? identitySessionId = null,Object? name = null,Object? state = null,Object? domainCommitId = null,Object? experienceSessions = null,}) {
  return _then(_self.copyWith(
interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,state: null == state ? _self.state : state // ignore: cast_nullable_to_non_nullable
as String,domainCommitId: null == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessions: null == experienceSessions ? _self.experienceSessions : experienceSessions // ignore: cast_nullable_to_non_nullable
as List<InterfaceSessionExperienceSessionView>,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceSessionView].
extension InterfaceSessionViewPatterns on InterfaceSessionView {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceSessionView value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceSessionView() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceSessionView value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionView():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceSessionView value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionView() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state, @UuidValueConverter()  UuidValue domainCommitId,  List<InterfaceSessionExperienceSessionView> experienceSessions)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceSessionView() when def != null:
return def(_that.interfaceSessionId,_that.interfaceId,_that.identitySessionId,_that.name,_that.state,_that.domainCommitId,_that.experienceSessions);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state, @UuidValueConverter()  UuidValue domainCommitId,  List<InterfaceSessionExperienceSessionView> experienceSessions)  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionView():
return def(_that.interfaceSessionId,_that.interfaceId,_that.identitySessionId,_that.name,_that.state,_that.domainCommitId,_that.experienceSessions);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue interfaceId, @UuidValueConverter()  UuidValue identitySessionId,  String name,  String state, @UuidValueConverter()  UuidValue domainCommitId,  List<InterfaceSessionExperienceSessionView> experienceSessions)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionView() when def != null:
return def(_that.interfaceSessionId,_that.interfaceId,_that.identitySessionId,_that.name,_that.state,_that.domainCommitId,_that.experienceSessions);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceSessionView implements InterfaceSessionView {
   _InterfaceSessionView({@UuidValueConverter() required this.interfaceSessionId, @UuidValueConverter() required this.interfaceId, @UuidValueConverter() required this.identitySessionId, required this.name, required this.state, @UuidValueConverter() required this.domainCommitId, final  List<InterfaceSessionExperienceSessionView> experienceSessions = const []}): _experienceSessions = experienceSessions;
  factory _InterfaceSessionView.fromJson(Map<String, dynamic> json) => _$InterfaceSessionViewFromJson(json);

@override@UuidValueConverter() final  UuidValue interfaceSessionId;
@override@UuidValueConverter() final  UuidValue interfaceId;
@override@UuidValueConverter() final  UuidValue identitySessionId;
@override final  String name;
@override final  String state;
@override@UuidValueConverter() final  UuidValue domainCommitId;
 final  List<InterfaceSessionExperienceSessionView> _experienceSessions;
@override@JsonKey() List<InterfaceSessionExperienceSessionView> get experienceSessions {
  if (_experienceSessions is EqualUnmodifiableListView) return _experienceSessions;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_experienceSessions);
}


/// Create a copy of InterfaceSessionView
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceSessionViewCopyWith<_InterfaceSessionView> get copyWith => __$InterfaceSessionViewCopyWithImpl<_InterfaceSessionView>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionViewToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceSessionView&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.interfaceId, interfaceId) || other.interfaceId == interfaceId)&&(identical(other.identitySessionId, identitySessionId) || other.identitySessionId == identitySessionId)&&(identical(other.name, name) || other.name == name)&&(identical(other.state, state) || other.state == state)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&const DeepCollectionEquality().equals(other._experienceSessions, _experienceSessions));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,interfaceSessionId,interfaceId,identitySessionId,name,state,domainCommitId,const DeepCollectionEquality().hash(_experienceSessions));

@override
String toString() {
  return 'InterfaceSessionView.def(interfaceSessionId: $interfaceSessionId, interfaceId: $interfaceId, identitySessionId: $identitySessionId, name: $name, state: $state, domainCommitId: $domainCommitId, experienceSessions: $experienceSessions)';
}


}

/// @nodoc
abstract mixin class _$InterfaceSessionViewCopyWith<$Res> implements $InterfaceSessionViewCopyWith<$Res> {
  factory _$InterfaceSessionViewCopyWith(_InterfaceSessionView value, $Res Function(_InterfaceSessionView) _then) = __$InterfaceSessionViewCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue interfaceSessionId,@UuidValueConverter() UuidValue interfaceId,@UuidValueConverter() UuidValue identitySessionId, String name, String state,@UuidValueConverter() UuidValue domainCommitId, List<InterfaceSessionExperienceSessionView> experienceSessions
});




}
/// @nodoc
class __$InterfaceSessionViewCopyWithImpl<$Res>
    implements _$InterfaceSessionViewCopyWith<$Res> {
  __$InterfaceSessionViewCopyWithImpl(this._self, this._then);

  final _InterfaceSessionView _self;
  final $Res Function(_InterfaceSessionView) _then;

/// Create a copy of InterfaceSessionView
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? interfaceSessionId = null,Object? interfaceId = null,Object? identitySessionId = null,Object? name = null,Object? state = null,Object? domainCommitId = null,Object? experienceSessions = null,}) {
  return _then(_InterfaceSessionView(
interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfaceId: null == interfaceId ? _self.interfaceId : interfaceId // ignore: cast_nullable_to_non_nullable
as UuidValue,identitySessionId: null == identitySessionId ? _self.identitySessionId : identitySessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,state: null == state ? _self.state : state // ignore: cast_nullable_to_non_nullable
as String,domainCommitId: null == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessions: null == experienceSessions ? _self._experienceSessions : experienceSessions // ignore: cast_nullable_to_non_nullable
as List<InterfaceSessionExperienceSessionView>,
  ));
}


}


/// @nodoc
mixin _$InterfaceSessionDescribeResponse {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion; bool get success; String? get error; String get status; InterfaceSessionView? get session;
/// Create a copy of InterfaceSessionDescribeResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceSessionDescribeResponseCopyWith<InterfaceSessionDescribeResponse> get copyWith => _$InterfaceSessionDescribeResponseCopyWithImpl<InterfaceSessionDescribeResponse>(this as InterfaceSessionDescribeResponse, _$identity);

  /// Serializes this InterfaceSessionDescribeResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceSessionDescribeResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.status, status) || other.status == status)&&(identical(other.session, session) || other.session == session));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,status,session);

@override
String toString() {
  return 'InterfaceSessionDescribeResponse(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, status: $status, session: $session)';
}


}

/// @nodoc
abstract mixin class $InterfaceSessionDescribeResponseCopyWith<$Res>  {
  factory $InterfaceSessionDescribeResponseCopyWith(InterfaceSessionDescribeResponse value, $Res Function(InterfaceSessionDescribeResponse) _then) = _$InterfaceSessionDescribeResponseCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String status, InterfaceSessionView? session
});


$InterfaceSessionViewCopyWith<$Res>? get session;

}
/// @nodoc
class _$InterfaceSessionDescribeResponseCopyWithImpl<$Res>
    implements $InterfaceSessionDescribeResponseCopyWith<$Res> {
  _$InterfaceSessionDescribeResponseCopyWithImpl(this._self, this._then);

  final InterfaceSessionDescribeResponse _self;
  final $Res Function(InterfaceSessionDescribeResponse) _then;

/// Create a copy of InterfaceSessionDescribeResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? status = null,Object? session = freezed,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,session: freezed == session ? _self.session : session // ignore: cast_nullable_to_non_nullable
as InterfaceSessionView?,
  ));
}
/// Create a copy of InterfaceSessionDescribeResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceSessionViewCopyWith<$Res>? get session {
    if (_self.session == null) {
    return null;
  }

  return $InterfaceSessionViewCopyWith<$Res>(_self.session!, (value) {
    return _then(_self.copyWith(session: value));
  });
}
}


/// Adds pattern-matching-related methods to [InterfaceSessionDescribeResponse].
extension InterfaceSessionDescribeResponsePatterns on InterfaceSessionDescribeResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceSessionDescribeResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceSessionDescribeResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceSessionDescribeResponse value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionDescribeResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceSessionDescribeResponse value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceSessionDescribeResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String status,  InterfaceSessionView? session)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceSessionDescribeResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.status,_that.session);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String status,  InterfaceSessionView? session)  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionDescribeResponse():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.status,_that.session);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String status,  InterfaceSessionView? session)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceSessionDescribeResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.status,_that.session);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceSessionDescribeResponse implements InterfaceSessionDescribeResponse {
   _InterfaceSessionDescribeResponse({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.status, this.session});
  factory _InterfaceSessionDescribeResponse.fromJson(Map<String, dynamic> json) => _$InterfaceSessionDescribeResponseFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
@override final  String status;
@override final  InterfaceSessionView? session;

/// Create a copy of InterfaceSessionDescribeResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceSessionDescribeResponseCopyWith<_InterfaceSessionDescribeResponse> get copyWith => __$InterfaceSessionDescribeResponseCopyWithImpl<_InterfaceSessionDescribeResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceSessionDescribeResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceSessionDescribeResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.status, status) || other.status == status)&&(identical(other.session, session) || other.session == session));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,status,session);

@override
String toString() {
  return 'InterfaceSessionDescribeResponse.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, status: $status, session: $session)';
}


}

/// @nodoc
abstract mixin class _$InterfaceSessionDescribeResponseCopyWith<$Res> implements $InterfaceSessionDescribeResponseCopyWith<$Res> {
  factory _$InterfaceSessionDescribeResponseCopyWith(_InterfaceSessionDescribeResponse value, $Res Function(_InterfaceSessionDescribeResponse) _then) = __$InterfaceSessionDescribeResponseCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String status, InterfaceSessionView? session
});


@override $InterfaceSessionViewCopyWith<$Res>? get session;

}
/// @nodoc
class __$InterfaceSessionDescribeResponseCopyWithImpl<$Res>
    implements _$InterfaceSessionDescribeResponseCopyWith<$Res> {
  __$InterfaceSessionDescribeResponseCopyWithImpl(this._self, this._then);

  final _InterfaceSessionDescribeResponse _self;
  final $Res Function(_InterfaceSessionDescribeResponse) _then;

/// Create a copy of InterfaceSessionDescribeResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? status = null,Object? session = freezed,}) {
  return _then(_InterfaceSessionDescribeResponse(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,session: freezed == session ? _self.session : session // ignore: cast_nullable_to_non_nullable
as InterfaceSessionView?,
  ));
}

/// Create a copy of InterfaceSessionDescribeResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceSessionViewCopyWith<$Res>? get session {
    if (_self.session == null) {
    return null;
  }

  return $InterfaceSessionViewCopyWith<$Res>(_self.session!, (value) {
    return _then(_self.copyWith(session: value));
  });
}
}


/// @nodoc
mixin _$InterfaceExperienceSessionMountRequest {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion;@UuidValueConverter() UuidValue get interfaceSessionId;@UuidValueConverter() UuidValue get experienceSessionId; String get status; Map<String, dynamic>? get metadataJson;
/// Create a copy of InterfaceExperienceSessionMountRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceExperienceSessionMountRequestCopyWith<InterfaceExperienceSessionMountRequest> get copyWith => _$InterfaceExperienceSessionMountRequestCopyWithImpl<InterfaceExperienceSessionMountRequest>(this as InterfaceExperienceSessionMountRequest, _$identity);

  /// Serializes this InterfaceExperienceSessionMountRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceExperienceSessionMountRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.experienceSessionId, experienceSessionId) || other.experienceSessionId == experienceSessionId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,interfaceSessionId,experienceSessionId,status,const DeepCollectionEquality().hash(metadataJson));

@override
String toString() {
  return 'InterfaceExperienceSessionMountRequest(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, interfaceSessionId: $interfaceSessionId, experienceSessionId: $experienceSessionId, status: $status, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class $InterfaceExperienceSessionMountRequestCopyWith<$Res>  {
  factory $InterfaceExperienceSessionMountRequestCopyWith(InterfaceExperienceSessionMountRequest value, $Res Function(InterfaceExperienceSessionMountRequest) _then) = _$InterfaceExperienceSessionMountRequestCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion,@UuidValueConverter() UuidValue interfaceSessionId,@UuidValueConverter() UuidValue experienceSessionId, String status, Map<String, dynamic>? metadataJson
});




}
/// @nodoc
class _$InterfaceExperienceSessionMountRequestCopyWithImpl<$Res>
    implements $InterfaceExperienceSessionMountRequestCopyWith<$Res> {
  _$InterfaceExperienceSessionMountRequestCopyWithImpl(this._self, this._then);

  final InterfaceExperienceSessionMountRequest _self;
  final $Res Function(InterfaceExperienceSessionMountRequest) _then;

/// Create a copy of InterfaceExperienceSessionMountRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? interfaceSessionId = null,Object? experienceSessionId = null,Object? status = null,Object? metadataJson = freezed,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessionId: null == experienceSessionId ? _self.experienceSessionId : experienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: freezed == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceExperienceSessionMountRequest].
extension InterfaceExperienceSessionMountRequestPatterns on InterfaceExperienceSessionMountRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceExperienceSessionMountRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceExperienceSessionMountRequest value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceExperienceSessionMountRequest value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson)  def,}) {final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountRequest():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.interfaceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceExperienceSessionMountRequest implements InterfaceExperienceSessionMountRequest {
   _InterfaceExperienceSessionMountRequest({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, @UuidValueConverter() required this.interfaceSessionId, @UuidValueConverter() required this.experienceSessionId, required this.status, final  Map<String, dynamic>? metadataJson}): _metadataJson = metadataJson;
  factory _InterfaceExperienceSessionMountRequest.fromJson(Map<String, dynamic> json) => _$InterfaceExperienceSessionMountRequestFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override@UuidValueConverter() final  UuidValue interfaceSessionId;
@override@UuidValueConverter() final  UuidValue experienceSessionId;
@override final  String status;
 final  Map<String, dynamic>? _metadataJson;
@override Map<String, dynamic>? get metadataJson {
  final value = _metadataJson;
  if (value == null) return null;
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(value);
}


/// Create a copy of InterfaceExperienceSessionMountRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceExperienceSessionMountRequestCopyWith<_InterfaceExperienceSessionMountRequest> get copyWith => __$InterfaceExperienceSessionMountRequestCopyWithImpl<_InterfaceExperienceSessionMountRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceExperienceSessionMountRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceExperienceSessionMountRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.experienceSessionId, experienceSessionId) || other.experienceSessionId == experienceSessionId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,interfaceSessionId,experienceSessionId,status,const DeepCollectionEquality().hash(_metadataJson));

@override
String toString() {
  return 'InterfaceExperienceSessionMountRequest.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, interfaceSessionId: $interfaceSessionId, experienceSessionId: $experienceSessionId, status: $status, metadataJson: $metadataJson)';
}


}

/// @nodoc
abstract mixin class _$InterfaceExperienceSessionMountRequestCopyWith<$Res> implements $InterfaceExperienceSessionMountRequestCopyWith<$Res> {
  factory _$InterfaceExperienceSessionMountRequestCopyWith(_InterfaceExperienceSessionMountRequest value, $Res Function(_InterfaceExperienceSessionMountRequest) _then) = __$InterfaceExperienceSessionMountRequestCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion,@UuidValueConverter() UuidValue interfaceSessionId,@UuidValueConverter() UuidValue experienceSessionId, String status, Map<String, dynamic>? metadataJson
});




}
/// @nodoc
class __$InterfaceExperienceSessionMountRequestCopyWithImpl<$Res>
    implements _$InterfaceExperienceSessionMountRequestCopyWith<$Res> {
  __$InterfaceExperienceSessionMountRequestCopyWithImpl(this._self, this._then);

  final _InterfaceExperienceSessionMountRequest _self;
  final $Res Function(_InterfaceExperienceSessionMountRequest) _then;

/// Create a copy of InterfaceExperienceSessionMountRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? interfaceSessionId = null,Object? experienceSessionId = null,Object? status = null,Object? metadataJson = freezed,}) {
  return _then(_InterfaceExperienceSessionMountRequest(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessionId: null == experienceSessionId ? _self.experienceSessionId : experienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: freezed == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,
  ));
}


}


/// @nodoc
mixin _$InterfaceExperienceSessionMountResponse {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion; bool get success; String? get error;@UuidValueConverter() UuidValue get interfaceSessionExperienceSessionId;@UuidValueConverter() UuidValue get interfaceSessionId;@UuidValueConverter() UuidValue get experienceSessionId; String get status; Map<String, dynamic>? get metadataJson;@UuidValueConverter() UuidValue? get domainCommitId;@UuidValueConverter() UuidValue? get objectInstanceGraphCommitId; String? get graphHashPost;
/// Create a copy of InterfaceExperienceSessionMountResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceExperienceSessionMountResponseCopyWith<InterfaceExperienceSessionMountResponse> get copyWith => _$InterfaceExperienceSessionMountResponseCopyWithImpl<InterfaceExperienceSessionMountResponse>(this as InterfaceExperienceSessionMountResponse, _$identity);

  /// Serializes this InterfaceExperienceSessionMountResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceExperienceSessionMountResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.interfaceSessionExperienceSessionId, interfaceSessionExperienceSessionId) || other.interfaceSessionExperienceSessionId == interfaceSessionExperienceSessionId)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.experienceSessionId, experienceSessionId) || other.experienceSessionId == experienceSessionId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other.metadataJson, metadataJson)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,interfaceSessionExperienceSessionId,interfaceSessionId,experienceSessionId,status,const DeepCollectionEquality().hash(metadataJson),domainCommitId,objectInstanceGraphCommitId,graphHashPost);

@override
String toString() {
  return 'InterfaceExperienceSessionMountResponse(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, interfaceSessionExperienceSessionId: $interfaceSessionExperienceSessionId, interfaceSessionId: $interfaceSessionId, experienceSessionId: $experienceSessionId, status: $status, metadataJson: $metadataJson, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost)';
}


}

/// @nodoc
abstract mixin class $InterfaceExperienceSessionMountResponseCopyWith<$Res>  {
  factory $InterfaceExperienceSessionMountResponseCopyWith(InterfaceExperienceSessionMountResponse value, $Res Function(InterfaceExperienceSessionMountResponse) _then) = _$InterfaceExperienceSessionMountResponseCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error,@UuidValueConverter() UuidValue interfaceSessionExperienceSessionId,@UuidValueConverter() UuidValue interfaceSessionId,@UuidValueConverter() UuidValue experienceSessionId, String status, Map<String, dynamic>? metadataJson,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost
});




}
/// @nodoc
class _$InterfaceExperienceSessionMountResponseCopyWithImpl<$Res>
    implements $InterfaceExperienceSessionMountResponseCopyWith<$Res> {
  _$InterfaceExperienceSessionMountResponseCopyWithImpl(this._self, this._then);

  final InterfaceExperienceSessionMountResponse _self;
  final $Res Function(InterfaceExperienceSessionMountResponse) _then;

/// Create a copy of InterfaceExperienceSessionMountResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? interfaceSessionExperienceSessionId = null,Object? interfaceSessionId = null,Object? experienceSessionId = null,Object? status = null,Object? metadataJson = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,interfaceSessionExperienceSessionId: null == interfaceSessionExperienceSessionId ? _self.interfaceSessionExperienceSessionId : interfaceSessionExperienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessionId: null == experienceSessionId ? _self.experienceSessionId : experienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: freezed == metadataJson ? _self.metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceExperienceSessionMountResponse].
extension InterfaceExperienceSessionMountResponsePatterns on InterfaceExperienceSessionMountResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceExperienceSessionMountResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceExperienceSessionMountResponse value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceExperienceSessionMountResponse value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error, @UuidValueConverter()  UuidValue interfaceSessionExperienceSessionId, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.interfaceSessionExperienceSessionId,_that.interfaceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.graphHashPost);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error, @UuidValueConverter()  UuidValue interfaceSessionExperienceSessionId, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost)  def,}) {final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountResponse():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.interfaceSessionExperienceSessionId,_that.interfaceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.graphHashPost);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error, @UuidValueConverter()  UuidValue interfaceSessionExperienceSessionId, @UuidValueConverter()  UuidValue interfaceSessionId, @UuidValueConverter()  UuidValue experienceSessionId,  String status,  Map<String, dynamic>? metadataJson, @UuidValueConverter()  UuidValue? domainCommitId, @UuidValueConverter()  UuidValue? objectInstanceGraphCommitId,  String? graphHashPost)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceExperienceSessionMountResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.interfaceSessionExperienceSessionId,_that.interfaceSessionId,_that.experienceSessionId,_that.status,_that.metadataJson,_that.domainCommitId,_that.objectInstanceGraphCommitId,_that.graphHashPost);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceExperienceSessionMountResponse implements InterfaceExperienceSessionMountResponse {
   _InterfaceExperienceSessionMountResponse({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, @UuidValueConverter() required this.interfaceSessionExperienceSessionId, @UuidValueConverter() required this.interfaceSessionId, @UuidValueConverter() required this.experienceSessionId, required this.status, final  Map<String, dynamic>? metadataJson, @UuidValueConverter() this.domainCommitId, @UuidValueConverter() this.objectInstanceGraphCommitId, this.graphHashPost}): _metadataJson = metadataJson;
  factory _InterfaceExperienceSessionMountResponse.fromJson(Map<String, dynamic> json) => _$InterfaceExperienceSessionMountResponseFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
@override@UuidValueConverter() final  UuidValue interfaceSessionExperienceSessionId;
@override@UuidValueConverter() final  UuidValue interfaceSessionId;
@override@UuidValueConverter() final  UuidValue experienceSessionId;
@override final  String status;
 final  Map<String, dynamic>? _metadataJson;
@override Map<String, dynamic>? get metadataJson {
  final value = _metadataJson;
  if (value == null) return null;
  if (_metadataJson is EqualUnmodifiableMapView) return _metadataJson;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(value);
}

@override@UuidValueConverter() final  UuidValue? domainCommitId;
@override@UuidValueConverter() final  UuidValue? objectInstanceGraphCommitId;
@override final  String? graphHashPost;

/// Create a copy of InterfaceExperienceSessionMountResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceExperienceSessionMountResponseCopyWith<_InterfaceExperienceSessionMountResponse> get copyWith => __$InterfaceExperienceSessionMountResponseCopyWithImpl<_InterfaceExperienceSessionMountResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceExperienceSessionMountResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceExperienceSessionMountResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.interfaceSessionExperienceSessionId, interfaceSessionExperienceSessionId) || other.interfaceSessionExperienceSessionId == interfaceSessionExperienceSessionId)&&(identical(other.interfaceSessionId, interfaceSessionId) || other.interfaceSessionId == interfaceSessionId)&&(identical(other.experienceSessionId, experienceSessionId) || other.experienceSessionId == experienceSessionId)&&(identical(other.status, status) || other.status == status)&&const DeepCollectionEquality().equals(other._metadataJson, _metadataJson)&&(identical(other.domainCommitId, domainCommitId) || other.domainCommitId == domainCommitId)&&(identical(other.objectInstanceGraphCommitId, objectInstanceGraphCommitId) || other.objectInstanceGraphCommitId == objectInstanceGraphCommitId)&&(identical(other.graphHashPost, graphHashPost) || other.graphHashPost == graphHashPost));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,interfaceSessionExperienceSessionId,interfaceSessionId,experienceSessionId,status,const DeepCollectionEquality().hash(_metadataJson),domainCommitId,objectInstanceGraphCommitId,graphHashPost);

@override
String toString() {
  return 'InterfaceExperienceSessionMountResponse.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, interfaceSessionExperienceSessionId: $interfaceSessionExperienceSessionId, interfaceSessionId: $interfaceSessionId, experienceSessionId: $experienceSessionId, status: $status, metadataJson: $metadataJson, domainCommitId: $domainCommitId, objectInstanceGraphCommitId: $objectInstanceGraphCommitId, graphHashPost: $graphHashPost)';
}


}

/// @nodoc
abstract mixin class _$InterfaceExperienceSessionMountResponseCopyWith<$Res> implements $InterfaceExperienceSessionMountResponseCopyWith<$Res> {
  factory _$InterfaceExperienceSessionMountResponseCopyWith(_InterfaceExperienceSessionMountResponse value, $Res Function(_InterfaceExperienceSessionMountResponse) _then) = __$InterfaceExperienceSessionMountResponseCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error,@UuidValueConverter() UuidValue interfaceSessionExperienceSessionId,@UuidValueConverter() UuidValue interfaceSessionId,@UuidValueConverter() UuidValue experienceSessionId, String status, Map<String, dynamic>? metadataJson,@UuidValueConverter() UuidValue? domainCommitId,@UuidValueConverter() UuidValue? objectInstanceGraphCommitId, String? graphHashPost
});




}
/// @nodoc
class __$InterfaceExperienceSessionMountResponseCopyWithImpl<$Res>
    implements _$InterfaceExperienceSessionMountResponseCopyWith<$Res> {
  __$InterfaceExperienceSessionMountResponseCopyWithImpl(this._self, this._then);

  final _InterfaceExperienceSessionMountResponse _self;
  final $Res Function(_InterfaceExperienceSessionMountResponse) _then;

/// Create a copy of InterfaceExperienceSessionMountResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? interfaceSessionExperienceSessionId = null,Object? interfaceSessionId = null,Object? experienceSessionId = null,Object? status = null,Object? metadataJson = freezed,Object? domainCommitId = freezed,Object? objectInstanceGraphCommitId = freezed,Object? graphHashPost = freezed,}) {
  return _then(_InterfaceExperienceSessionMountResponse(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,interfaceSessionExperienceSessionId: null == interfaceSessionExperienceSessionId ? _self.interfaceSessionExperienceSessionId : interfaceSessionExperienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,interfaceSessionId: null == interfaceSessionId ? _self.interfaceSessionId : interfaceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,experienceSessionId: null == experienceSessionId ? _self.experienceSessionId : experienceSessionId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,metadataJson: freezed == metadataJson ? _self._metadataJson : metadataJson // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>?,domainCommitId: freezed == domainCommitId ? _self.domainCommitId : domainCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,objectInstanceGraphCommitId: freezed == objectInstanceGraphCommitId ? _self.objectInstanceGraphCommitId : objectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,graphHashPost: freezed == graphHashPost ? _self.graphHashPost : graphHashPost // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$InterfaceEnterAppScreenRequest {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion; String get namespace;@UuidValueConverter() UuidValue get appPackageId;@UuidValueConverter() UuidValue get appPackageBranchId;@UuidValueConverter() UuidValue get appPackageObjectInstanceGraphCommitId;@UuidValueConverter() UuidValue get appConfigScreenConfigId; String? get reason; Map<String, dynamic> get evidence;
/// Create a copy of InterfaceEnterAppScreenRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceEnterAppScreenRequestCopyWith<InterfaceEnterAppScreenRequest> get copyWith => _$InterfaceEnterAppScreenRequestCopyWithImpl<InterfaceEnterAppScreenRequest>(this as InterfaceEnterAppScreenRequest, _$identity);

  /// Serializes this InterfaceEnterAppScreenRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceEnterAppScreenRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.appPackageId, appPackageId) || other.appPackageId == appPackageId)&&(identical(other.appPackageBranchId, appPackageBranchId) || other.appPackageBranchId == appPackageBranchId)&&(identical(other.appPackageObjectInstanceGraphCommitId, appPackageObjectInstanceGraphCommitId) || other.appPackageObjectInstanceGraphCommitId == appPackageObjectInstanceGraphCommitId)&&(identical(other.appConfigScreenConfigId, appConfigScreenConfigId) || other.appConfigScreenConfigId == appConfigScreenConfigId)&&(identical(other.reason, reason) || other.reason == reason)&&const DeepCollectionEquality().equals(other.evidence, evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,namespace,appPackageId,appPackageBranchId,appPackageObjectInstanceGraphCommitId,appConfigScreenConfigId,reason,const DeepCollectionEquality().hash(evidence));

@override
String toString() {
  return 'InterfaceEnterAppScreenRequest(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, appPackageId: $appPackageId, appPackageBranchId: $appPackageBranchId, appPackageObjectInstanceGraphCommitId: $appPackageObjectInstanceGraphCommitId, appConfigScreenConfigId: $appConfigScreenConfigId, reason: $reason, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class $InterfaceEnterAppScreenRequestCopyWith<$Res>  {
  factory $InterfaceEnterAppScreenRequestCopyWith(InterfaceEnterAppScreenRequest value, $Res Function(InterfaceEnterAppScreenRequest) _then) = _$InterfaceEnterAppScreenRequestCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue appPackageId,@UuidValueConverter() UuidValue appPackageBranchId,@UuidValueConverter() UuidValue appPackageObjectInstanceGraphCommitId,@UuidValueConverter() UuidValue appConfigScreenConfigId, String? reason, Map<String, dynamic> evidence
});




}
/// @nodoc
class _$InterfaceEnterAppScreenRequestCopyWithImpl<$Res>
    implements $InterfaceEnterAppScreenRequestCopyWith<$Res> {
  _$InterfaceEnterAppScreenRequestCopyWithImpl(this._self, this._then);

  final InterfaceEnterAppScreenRequest _self;
  final $Res Function(InterfaceEnterAppScreenRequest) _then;

/// Create a copy of InterfaceEnterAppScreenRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? appPackageId = null,Object? appPackageBranchId = null,Object? appPackageObjectInstanceGraphCommitId = null,Object? appConfigScreenConfigId = null,Object? reason = freezed,Object? evidence = null,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,appPackageId: null == appPackageId ? _self.appPackageId : appPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,appPackageBranchId: null == appPackageBranchId ? _self.appPackageBranchId : appPackageBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue,appPackageObjectInstanceGraphCommitId: null == appPackageObjectInstanceGraphCommitId ? _self.appPackageObjectInstanceGraphCommitId : appPackageObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,appConfigScreenConfigId: null == appConfigScreenConfigId ? _self.appConfigScreenConfigId : appConfigScreenConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self.evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceEnterAppScreenRequest].
extension InterfaceEnterAppScreenRequestPatterns on InterfaceEnterAppScreenRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceEnterAppScreenRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceEnterAppScreenRequest value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceEnterAppScreenRequest value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue appPackageId, @UuidValueConverter()  UuidValue appPackageBranchId, @UuidValueConverter()  UuidValue appPackageObjectInstanceGraphCommitId, @UuidValueConverter()  UuidValue appConfigScreenConfigId,  String? reason,  Map<String, dynamic> evidence)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.namespace,_that.appPackageId,_that.appPackageBranchId,_that.appPackageObjectInstanceGraphCommitId,_that.appConfigScreenConfigId,_that.reason,_that.evidence);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue appPackageId, @UuidValueConverter()  UuidValue appPackageBranchId, @UuidValueConverter()  UuidValue appPackageObjectInstanceGraphCommitId, @UuidValueConverter()  UuidValue appConfigScreenConfigId,  String? reason,  Map<String, dynamic> evidence)  def,}) {final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenRequest():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.namespace,_that.appPackageId,_that.appPackageBranchId,_that.appPackageObjectInstanceGraphCommitId,_that.appConfigScreenConfigId,_that.reason,_that.evidence);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  String namespace, @UuidValueConverter()  UuidValue appPackageId, @UuidValueConverter()  UuidValue appPackageBranchId, @UuidValueConverter()  UuidValue appPackageObjectInstanceGraphCommitId, @UuidValueConverter()  UuidValue appConfigScreenConfigId,  String? reason,  Map<String, dynamic> evidence)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenRequest() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.namespace,_that.appPackageId,_that.appPackageBranchId,_that.appPackageObjectInstanceGraphCommitId,_that.appConfigScreenConfigId,_that.reason,_that.evidence);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceEnterAppScreenRequest implements InterfaceEnterAppScreenRequest {
   _InterfaceEnterAppScreenRequest({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, required this.namespace, @UuidValueConverter() required this.appPackageId, @UuidValueConverter() required this.appPackageBranchId, @UuidValueConverter() required this.appPackageObjectInstanceGraphCommitId, @UuidValueConverter() required this.appConfigScreenConfigId, this.reason, required final  Map<String, dynamic> evidence}): _evidence = evidence;
  factory _InterfaceEnterAppScreenRequest.fromJson(Map<String, dynamic> json) => _$InterfaceEnterAppScreenRequestFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  String namespace;
@override@UuidValueConverter() final  UuidValue appPackageId;
@override@UuidValueConverter() final  UuidValue appPackageBranchId;
@override@UuidValueConverter() final  UuidValue appPackageObjectInstanceGraphCommitId;
@override@UuidValueConverter() final  UuidValue appConfigScreenConfigId;
@override final  String? reason;
 final  Map<String, dynamic> _evidence;
@override Map<String, dynamic> get evidence {
  if (_evidence is EqualUnmodifiableMapView) return _evidence;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_evidence);
}


/// Create a copy of InterfaceEnterAppScreenRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceEnterAppScreenRequestCopyWith<_InterfaceEnterAppScreenRequest> get copyWith => __$InterfaceEnterAppScreenRequestCopyWithImpl<_InterfaceEnterAppScreenRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceEnterAppScreenRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceEnterAppScreenRequest&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.appPackageId, appPackageId) || other.appPackageId == appPackageId)&&(identical(other.appPackageBranchId, appPackageBranchId) || other.appPackageBranchId == appPackageBranchId)&&(identical(other.appPackageObjectInstanceGraphCommitId, appPackageObjectInstanceGraphCommitId) || other.appPackageObjectInstanceGraphCommitId == appPackageObjectInstanceGraphCommitId)&&(identical(other.appConfigScreenConfigId, appConfigScreenConfigId) || other.appConfigScreenConfigId == appConfigScreenConfigId)&&(identical(other.reason, reason) || other.reason == reason)&&const DeepCollectionEquality().equals(other._evidence, _evidence));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,namespace,appPackageId,appPackageBranchId,appPackageObjectInstanceGraphCommitId,appConfigScreenConfigId,reason,const DeepCollectionEquality().hash(_evidence));

@override
String toString() {
  return 'InterfaceEnterAppScreenRequest.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, namespace: $namespace, appPackageId: $appPackageId, appPackageBranchId: $appPackageBranchId, appPackageObjectInstanceGraphCommitId: $appPackageObjectInstanceGraphCommitId, appConfigScreenConfigId: $appConfigScreenConfigId, reason: $reason, evidence: $evidence)';
}


}

/// @nodoc
abstract mixin class _$InterfaceEnterAppScreenRequestCopyWith<$Res> implements $InterfaceEnterAppScreenRequestCopyWith<$Res> {
  factory _$InterfaceEnterAppScreenRequestCopyWith(_InterfaceEnterAppScreenRequest value, $Res Function(_InterfaceEnterAppScreenRequest) _then) = __$InterfaceEnterAppScreenRequestCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, String namespace,@UuidValueConverter() UuidValue appPackageId,@UuidValueConverter() UuidValue appPackageBranchId,@UuidValueConverter() UuidValue appPackageObjectInstanceGraphCommitId,@UuidValueConverter() UuidValue appConfigScreenConfigId, String? reason, Map<String, dynamic> evidence
});




}
/// @nodoc
class __$InterfaceEnterAppScreenRequestCopyWithImpl<$Res>
    implements _$InterfaceEnterAppScreenRequestCopyWith<$Res> {
  __$InterfaceEnterAppScreenRequestCopyWithImpl(this._self, this._then);

  final _InterfaceEnterAppScreenRequest _self;
  final $Res Function(_InterfaceEnterAppScreenRequest) _then;

/// Create a copy of InterfaceEnterAppScreenRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? namespace = null,Object? appPackageId = null,Object? appPackageBranchId = null,Object? appPackageObjectInstanceGraphCommitId = null,Object? appConfigScreenConfigId = null,Object? reason = freezed,Object? evidence = null,}) {
  return _then(_InterfaceEnterAppScreenRequest(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,appPackageId: null == appPackageId ? _self.appPackageId : appPackageId // ignore: cast_nullable_to_non_nullable
as UuidValue,appPackageBranchId: null == appPackageBranchId ? _self.appPackageBranchId : appPackageBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue,appPackageObjectInstanceGraphCommitId: null == appPackageObjectInstanceGraphCommitId ? _self.appPackageObjectInstanceGraphCommitId : appPackageObjectInstanceGraphCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,appConfigScreenConfigId: null == appConfigScreenConfigId ? _self.appConfigScreenConfigId : appConfigScreenConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,reason: freezed == reason ? _self.reason : reason // ignore: cast_nullable_to_non_nullable
as String?,evidence: null == evidence ? _self._evidence : evidence // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,
  ));
}


}


/// @nodoc
mixin _$InterfaceEnterAppScreenResponse {

 String get operation;@UuidValueConverter() UuidValue? get requestId; int get protocolVersion; bool get success; String? get error; String get namespace; InterfaceAppScreenState? get appScreen; InterfaceHostState get hostState;
/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceEnterAppScreenResponseCopyWith<InterfaceEnterAppScreenResponse> get copyWith => _$InterfaceEnterAppScreenResponseCopyWithImpl<InterfaceEnterAppScreenResponse>(this as InterfaceEnterAppScreenResponse, _$identity);

  /// Serializes this InterfaceEnterAppScreenResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceEnterAppScreenResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.appScreen, appScreen) || other.appScreen == appScreen)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,namespace,appScreen,hostState);

@override
String toString() {
  return 'InterfaceEnterAppScreenResponse(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, appScreen: $appScreen, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class $InterfaceEnterAppScreenResponseCopyWith<$Res>  {
  factory $InterfaceEnterAppScreenResponseCopyWith(InterfaceEnterAppScreenResponse value, $Res Function(InterfaceEnterAppScreenResponse) _then) = _$InterfaceEnterAppScreenResponseCopyWithImpl;
@useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceAppScreenState? appScreen, InterfaceHostState hostState
});


$InterfaceAppScreenStateCopyWith<$Res>? get appScreen;$InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class _$InterfaceEnterAppScreenResponseCopyWithImpl<$Res>
    implements $InterfaceEnterAppScreenResponseCopyWith<$Res> {
  _$InterfaceEnterAppScreenResponseCopyWithImpl(this._self, this._then);

  final InterfaceEnterAppScreenResponse _self;
  final $Res Function(InterfaceEnterAppScreenResponse) _then;

/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? appScreen = freezed,Object? hostState = null,}) {
  return _then(_self.copyWith(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,appScreen: freezed == appScreen ? _self.appScreen : appScreen // ignore: cast_nullable_to_non_nullable
as InterfaceAppScreenState?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}
/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceAppScreenStateCopyWith<$Res>? get appScreen {
    if (_self.appScreen == null) {
    return null;
  }

  return $InterfaceAppScreenStateCopyWith<$Res>(_self.appScreen!, (value) {
    return _then(_self.copyWith(appScreen: value));
  });
}/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}


/// Adds pattern-matching-related methods to [InterfaceEnterAppScreenResponse].
extension InterfaceEnterAppScreenResponsePatterns on InterfaceEnterAppScreenResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceEnterAppScreenResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceEnterAppScreenResponse value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceEnterAppScreenResponse value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceAppScreenState? appScreen,  InterfaceHostState hostState)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.appScreen,_that.hostState);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceAppScreenState? appScreen,  InterfaceHostState hostState)  def,}) {final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenResponse():
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.appScreen,_that.hostState);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operation, @UuidValueConverter()  UuidValue? requestId,  int protocolVersion,  bool success,  String? error,  String namespace,  InterfaceAppScreenState? appScreen,  InterfaceHostState hostState)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceEnterAppScreenResponse() when def != null:
return def(_that.operation,_that.requestId,_that.protocolVersion,_that.success,_that.error,_that.namespace,_that.appScreen,_that.hostState);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceEnterAppScreenResponse implements InterfaceEnterAppScreenResponse {
   _InterfaceEnterAppScreenResponse({required this.operation, @UuidValueConverter() this.requestId, required this.protocolVersion, required this.success, this.error, required this.namespace, this.appScreen, required this.hostState});
  factory _InterfaceEnterAppScreenResponse.fromJson(Map<String, dynamic> json) => _$InterfaceEnterAppScreenResponseFromJson(json);

@override final  String operation;
@override@UuidValueConverter() final  UuidValue? requestId;
@override final  int protocolVersion;
@override final  bool success;
@override final  String? error;
@override final  String namespace;
@override final  InterfaceAppScreenState? appScreen;
@override final  InterfaceHostState hostState;

/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceEnterAppScreenResponseCopyWith<_InterfaceEnterAppScreenResponse> get copyWith => __$InterfaceEnterAppScreenResponseCopyWithImpl<_InterfaceEnterAppScreenResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceEnterAppScreenResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceEnterAppScreenResponse&&(identical(other.operation, operation) || other.operation == operation)&&(identical(other.requestId, requestId) || other.requestId == requestId)&&(identical(other.protocolVersion, protocolVersion) || other.protocolVersion == protocolVersion)&&(identical(other.success, success) || other.success == success)&&(identical(other.error, error) || other.error == error)&&(identical(other.namespace, namespace) || other.namespace == namespace)&&(identical(other.appScreen, appScreen) || other.appScreen == appScreen)&&(identical(other.hostState, hostState) || other.hostState == hostState));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operation,requestId,protocolVersion,success,error,namespace,appScreen,hostState);

@override
String toString() {
  return 'InterfaceEnterAppScreenResponse.def(operation: $operation, requestId: $requestId, protocolVersion: $protocolVersion, success: $success, error: $error, namespace: $namespace, appScreen: $appScreen, hostState: $hostState)';
}


}

/// @nodoc
abstract mixin class _$InterfaceEnterAppScreenResponseCopyWith<$Res> implements $InterfaceEnterAppScreenResponseCopyWith<$Res> {
  factory _$InterfaceEnterAppScreenResponseCopyWith(_InterfaceEnterAppScreenResponse value, $Res Function(_InterfaceEnterAppScreenResponse) _then) = __$InterfaceEnterAppScreenResponseCopyWithImpl;
@override @useResult
$Res call({
 String operation,@UuidValueConverter() UuidValue? requestId, int protocolVersion, bool success, String? error, String namespace, InterfaceAppScreenState? appScreen, InterfaceHostState hostState
});


@override $InterfaceAppScreenStateCopyWith<$Res>? get appScreen;@override $InterfaceHostStateCopyWith<$Res> get hostState;

}
/// @nodoc
class __$InterfaceEnterAppScreenResponseCopyWithImpl<$Res>
    implements _$InterfaceEnterAppScreenResponseCopyWith<$Res> {
  __$InterfaceEnterAppScreenResponseCopyWithImpl(this._self, this._then);

  final _InterfaceEnterAppScreenResponse _self;
  final $Res Function(_InterfaceEnterAppScreenResponse) _then;

/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operation = null,Object? requestId = freezed,Object? protocolVersion = null,Object? success = null,Object? error = freezed,Object? namespace = null,Object? appScreen = freezed,Object? hostState = null,}) {
  return _then(_InterfaceEnterAppScreenResponse(
operation: null == operation ? _self.operation : operation // ignore: cast_nullable_to_non_nullable
as String,requestId: freezed == requestId ? _self.requestId : requestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,protocolVersion: null == protocolVersion ? _self.protocolVersion : protocolVersion // ignore: cast_nullable_to_non_nullable
as int,success: null == success ? _self.success : success // ignore: cast_nullable_to_non_nullable
as bool,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,namespace: null == namespace ? _self.namespace : namespace // ignore: cast_nullable_to_non_nullable
as String,appScreen: freezed == appScreen ? _self.appScreen : appScreen // ignore: cast_nullable_to_non_nullable
as InterfaceAppScreenState?,hostState: null == hostState ? _self.hostState : hostState // ignore: cast_nullable_to_non_nullable
as InterfaceHostState,
  ));
}

/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceAppScreenStateCopyWith<$Res>? get appScreen {
    if (_self.appScreen == null) {
    return null;
  }

  return $InterfaceAppScreenStateCopyWith<$Res>(_self.appScreen!, (value) {
    return _then(_self.copyWith(appScreen: value));
  });
}/// Create a copy of InterfaceEnterAppScreenResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$InterfaceHostStateCopyWith<$Res> get hostState {
  
  return $InterfaceHostStateCopyWith<$Res>(_self.hostState, (value) {
    return _then(_self.copyWith(hostState: value));
  });
}
}


/// @nodoc
mixin _$InterfaceAttentionLayoutTransitionSectionIntent {

@UuidValueConverter() UuidValue get layoutConfigSectionConfigId; int get order; int get weightMicros; bool get isVisible; bool get isCollapsed;
/// Create a copy of InterfaceAttentionLayoutTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceAttentionLayoutTransitionSectionIntentCopyWith<InterfaceAttentionLayoutTransitionSectionIntent> get copyWith => _$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl<InterfaceAttentionLayoutTransitionSectionIntent>(this as InterfaceAttentionLayoutTransitionSectionIntent, _$identity);

  /// Serializes this InterfaceAttentionLayoutTransitionSectionIntent to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceAttentionLayoutTransitionSectionIntent&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId)&&(identical(other.order, order) || other.order == order)&&(identical(other.weightMicros, weightMicros) || other.weightMicros == weightMicros)&&(identical(other.isVisible, isVisible) || other.isVisible == isVisible)&&(identical(other.isCollapsed, isCollapsed) || other.isCollapsed == isCollapsed));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutConfigSectionConfigId,order,weightMicros,isVisible,isCollapsed);

@override
String toString() {
  return 'InterfaceAttentionLayoutTransitionSectionIntent(layoutConfigSectionConfigId: $layoutConfigSectionConfigId, order: $order, weightMicros: $weightMicros, isVisible: $isVisible, isCollapsed: $isCollapsed)';
}


}

/// @nodoc
abstract mixin class $InterfaceAttentionLayoutTransitionSectionIntentCopyWith<$Res>  {
  factory $InterfaceAttentionLayoutTransitionSectionIntentCopyWith(InterfaceAttentionLayoutTransitionSectionIntent value, $Res Function(InterfaceAttentionLayoutTransitionSectionIntent) _then) = _$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue layoutConfigSectionConfigId, int order, int weightMicros, bool isVisible, bool isCollapsed
});




}
/// @nodoc
class _$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl<$Res>
    implements $InterfaceAttentionLayoutTransitionSectionIntentCopyWith<$Res> {
  _$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl(this._self, this._then);

  final InterfaceAttentionLayoutTransitionSectionIntent _self;
  final $Res Function(InterfaceAttentionLayoutTransitionSectionIntent) _then;

/// Create a copy of InterfaceAttentionLayoutTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? layoutConfigSectionConfigId = null,Object? order = null,Object? weightMicros = null,Object? isVisible = null,Object? isCollapsed = null,}) {
  return _then(_self.copyWith(
layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,weightMicros: null == weightMicros ? _self.weightMicros : weightMicros // ignore: cast_nullable_to_non_nullable
as int,isVisible: null == isVisible ? _self.isVisible : isVisible // ignore: cast_nullable_to_non_nullable
as bool,isCollapsed: null == isCollapsed ? _self.isCollapsed : isCollapsed // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceAttentionLayoutTransitionSectionIntent].
extension InterfaceAttentionLayoutTransitionSectionIntentPatterns on InterfaceAttentionLayoutTransitionSectionIntent {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceAttentionLayoutTransitionSectionIntent value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTransitionSectionIntent() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceAttentionLayoutTransitionSectionIntent value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTransitionSectionIntent():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceAttentionLayoutTransitionSectionIntent value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTransitionSectionIntent() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  int order,  int weightMicros,  bool isVisible,  bool isCollapsed)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTransitionSectionIntent() when def != null:
return def(_that.layoutConfigSectionConfigId,_that.order,_that.weightMicros,_that.isVisible,_that.isCollapsed);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  int order,  int weightMicros,  bool isVisible,  bool isCollapsed)  def,}) {final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTransitionSectionIntent():
return def(_that.layoutConfigSectionConfigId,_that.order,_that.weightMicros,_that.isVisible,_that.isCollapsed);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  int order,  int weightMicros,  bool isVisible,  bool isCollapsed)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTransitionSectionIntent() when def != null:
return def(_that.layoutConfigSectionConfigId,_that.order,_that.weightMicros,_that.isVisible,_that.isCollapsed);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceAttentionLayoutTransitionSectionIntent implements InterfaceAttentionLayoutTransitionSectionIntent {
   _InterfaceAttentionLayoutTransitionSectionIntent({@UuidValueConverter() required this.layoutConfigSectionConfigId, required this.order, required this.weightMicros, required this.isVisible, required this.isCollapsed});
  factory _InterfaceAttentionLayoutTransitionSectionIntent.fromJson(Map<String, dynamic> json) => _$InterfaceAttentionLayoutTransitionSectionIntentFromJson(json);

@override@UuidValueConverter() final  UuidValue layoutConfigSectionConfigId;
@override final  int order;
@override final  int weightMicros;
@override final  bool isVisible;
@override final  bool isCollapsed;

/// Create a copy of InterfaceAttentionLayoutTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceAttentionLayoutTransitionSectionIntentCopyWith<_InterfaceAttentionLayoutTransitionSectionIntent> get copyWith => __$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl<_InterfaceAttentionLayoutTransitionSectionIntent>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceAttentionLayoutTransitionSectionIntentToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceAttentionLayoutTransitionSectionIntent&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId)&&(identical(other.order, order) || other.order == order)&&(identical(other.weightMicros, weightMicros) || other.weightMicros == weightMicros)&&(identical(other.isVisible, isVisible) || other.isVisible == isVisible)&&(identical(other.isCollapsed, isCollapsed) || other.isCollapsed == isCollapsed));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutConfigSectionConfigId,order,weightMicros,isVisible,isCollapsed);

@override
String toString() {
  return 'InterfaceAttentionLayoutTransitionSectionIntent.def(layoutConfigSectionConfigId: $layoutConfigSectionConfigId, order: $order, weightMicros: $weightMicros, isVisible: $isVisible, isCollapsed: $isCollapsed)';
}


}

/// @nodoc
abstract mixin class _$InterfaceAttentionLayoutTransitionSectionIntentCopyWith<$Res> implements $InterfaceAttentionLayoutTransitionSectionIntentCopyWith<$Res> {
  factory _$InterfaceAttentionLayoutTransitionSectionIntentCopyWith(_InterfaceAttentionLayoutTransitionSectionIntent value, $Res Function(_InterfaceAttentionLayoutTransitionSectionIntent) _then) = __$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue layoutConfigSectionConfigId, int order, int weightMicros, bool isVisible, bool isCollapsed
});




}
/// @nodoc
class __$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl<$Res>
    implements _$InterfaceAttentionLayoutTransitionSectionIntentCopyWith<$Res> {
  __$InterfaceAttentionLayoutTransitionSectionIntentCopyWithImpl(this._self, this._then);

  final _InterfaceAttentionLayoutTransitionSectionIntent _self;
  final $Res Function(_InterfaceAttentionLayoutTransitionSectionIntent) _then;

/// Create a copy of InterfaceAttentionLayoutTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? layoutConfigSectionConfigId = null,Object? order = null,Object? weightMicros = null,Object? isVisible = null,Object? isCollapsed = null,}) {
  return _then(_InterfaceAttentionLayoutTransitionSectionIntent(
layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,weightMicros: null == weightMicros ? _self.weightMicros : weightMicros // ignore: cast_nullable_to_non_nullable
as int,isVisible: null == isVisible ? _self.isVisible : isVisible // ignore: cast_nullable_to_non_nullable
as bool,isCollapsed: null == isCollapsed ? _self.isCollapsed : isCollapsed // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$InterfaceAttentionLayoutTopologyTransitionSectionIntent {

@UuidValueConverter() UuidValue get layoutConfigSectionConfigId; int get order;
/// Create a copy of InterfaceAttentionLayoutTopologyTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith<InterfaceAttentionLayoutTopologyTransitionSectionIntent> get copyWith => _$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl<InterfaceAttentionLayoutTopologyTransitionSectionIntent>(this as InterfaceAttentionLayoutTopologyTransitionSectionIntent, _$identity);

  /// Serializes this InterfaceAttentionLayoutTopologyTransitionSectionIntent to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is InterfaceAttentionLayoutTopologyTransitionSectionIntent&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId)&&(identical(other.order, order) || other.order == order));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutConfigSectionConfigId,order);

@override
String toString() {
  return 'InterfaceAttentionLayoutTopologyTransitionSectionIntent(layoutConfigSectionConfigId: $layoutConfigSectionConfigId, order: $order)';
}


}

/// @nodoc
abstract mixin class $InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith<$Res>  {
  factory $InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith(InterfaceAttentionLayoutTopologyTransitionSectionIntent value, $Res Function(InterfaceAttentionLayoutTopologyTransitionSectionIntent) _then) = _$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue layoutConfigSectionConfigId, int order
});




}
/// @nodoc
class _$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl<$Res>
    implements $InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith<$Res> {
  _$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl(this._self, this._then);

  final InterfaceAttentionLayoutTopologyTransitionSectionIntent _self;
  final $Res Function(InterfaceAttentionLayoutTopologyTransitionSectionIntent) _then;

/// Create a copy of InterfaceAttentionLayoutTopologyTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? layoutConfigSectionConfigId = null,Object? order = null,}) {
  return _then(_self.copyWith(
layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,
  ));
}

}


/// Adds pattern-matching-related methods to [InterfaceAttentionLayoutTopologyTransitionSectionIntent].
extension InterfaceAttentionLayoutTopologyTransitionSectionIntentPatterns on InterfaceAttentionLayoutTopologyTransitionSectionIntent {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _InterfaceAttentionLayoutTopologyTransitionSectionIntent value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTopologyTransitionSectionIntent() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _InterfaceAttentionLayoutTopologyTransitionSectionIntent value)  def,}){
final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTopologyTransitionSectionIntent():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _InterfaceAttentionLayoutTopologyTransitionSectionIntent value)?  def,}){
final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTopologyTransitionSectionIntent() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  int order)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTopologyTransitionSectionIntent() when def != null:
return def(_that.layoutConfigSectionConfigId,_that.order);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  int order)  def,}) {final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTopologyTransitionSectionIntent():
return def(_that.layoutConfigSectionConfigId,_that.order);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue layoutConfigSectionConfigId,  int order)?  def,}) {final _that = this;
switch (_that) {
case _InterfaceAttentionLayoutTopologyTransitionSectionIntent() when def != null:
return def(_that.layoutConfigSectionConfigId,_that.order);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _InterfaceAttentionLayoutTopologyTransitionSectionIntent implements InterfaceAttentionLayoutTopologyTransitionSectionIntent {
   _InterfaceAttentionLayoutTopologyTransitionSectionIntent({@UuidValueConverter() required this.layoutConfigSectionConfigId, required this.order});
  factory _InterfaceAttentionLayoutTopologyTransitionSectionIntent.fromJson(Map<String, dynamic> json) => _$InterfaceAttentionLayoutTopologyTransitionSectionIntentFromJson(json);

@override@UuidValueConverter() final  UuidValue layoutConfigSectionConfigId;
@override final  int order;

/// Create a copy of InterfaceAttentionLayoutTopologyTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith<_InterfaceAttentionLayoutTopologyTransitionSectionIntent> get copyWith => __$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl<_InterfaceAttentionLayoutTopologyTransitionSectionIntent>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$InterfaceAttentionLayoutTopologyTransitionSectionIntentToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _InterfaceAttentionLayoutTopologyTransitionSectionIntent&&(identical(other.layoutConfigSectionConfigId, layoutConfigSectionConfigId) || other.layoutConfigSectionConfigId == layoutConfigSectionConfigId)&&(identical(other.order, order) || other.order == order));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,layoutConfigSectionConfigId,order);

@override
String toString() {
  return 'InterfaceAttentionLayoutTopologyTransitionSectionIntent.def(layoutConfigSectionConfigId: $layoutConfigSectionConfigId, order: $order)';
}


}

/// @nodoc
abstract mixin class _$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith<$Res> implements $InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith<$Res> {
  factory _$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith(_InterfaceAttentionLayoutTopologyTransitionSectionIntent value, $Res Function(_InterfaceAttentionLayoutTopologyTransitionSectionIntent) _then) = __$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue layoutConfigSectionConfigId, int order
});




}
/// @nodoc
class __$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl<$Res>
    implements _$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWith<$Res> {
  __$InterfaceAttentionLayoutTopologyTransitionSectionIntentCopyWithImpl(this._self, this._then);

  final _InterfaceAttentionLayoutTopologyTransitionSectionIntent _self;
  final $Res Function(_InterfaceAttentionLayoutTopologyTransitionSectionIntent) _then;

/// Create a copy of InterfaceAttentionLayoutTopologyTransitionSectionIntent
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? layoutConfigSectionConfigId = null,Object? order = null,}) {
  return _then(_InterfaceAttentionLayoutTopologyTransitionSectionIntent(
layoutConfigSectionConfigId: null == layoutConfigSectionConfigId ? _self.layoutConfigSectionConfigId : layoutConfigSectionConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,order: null == order ? _self.order : order // ignore: cast_nullable_to_non_nullable
as int,
  ));
}


}

// dart format on
