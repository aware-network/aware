// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'service_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$ServiceOperationContext {

@UuidValueConverter() UuidValue? get actorId;@UuidValueConverter() UuidValue get branchId; String get projectionHash;
/// Create a copy of ServiceOperationContext
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceOperationContextCopyWith<ServiceOperationContext> get copyWith => _$ServiceOperationContextCopyWithImpl<ServiceOperationContext>(this as ServiceOperationContext, _$identity);

  /// Serializes this ServiceOperationContext to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,branchId,projectionHash);

@override
String toString() {
  return 'ServiceOperationContext(actorId: $actorId, branchId: $branchId, projectionHash: $projectionHash)';
}


}

/// @nodoc
abstract mixin class $ServiceOperationContextCopyWith<$Res>  {
  factory $ServiceOperationContextCopyWith(ServiceOperationContext value, $Res Function(ServiceOperationContext) _then) = _$ServiceOperationContextCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue branchId, String projectionHash
});




}
/// @nodoc
class _$ServiceOperationContextCopyWithImpl<$Res>
    implements $ServiceOperationContextCopyWith<$Res> {
  _$ServiceOperationContextCopyWithImpl(this._self, this._then);

  final ServiceOperationContext _self;
  final $Res Function(ServiceOperationContext) _then;

/// Create a copy of ServiceOperationContext
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? actorId = freezed,Object? branchId = null,Object? projectionHash = null,}) {
  return _then(_self.copyWith(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: null == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue,projectionHash: null == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String,
  ));
}

}


/// Adds pattern-matching-related methods to [ServiceOperationContext].
extension ServiceOperationContextPatterns on ServiceOperationContext {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceOperationContext value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceOperationContext() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceOperationContext value)  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationContext():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceOperationContext value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationContext() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue branchId,  String projectionHash)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceOperationContext() when def != null:
return def(_that.actorId,_that.branchId,_that.projectionHash);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue branchId,  String projectionHash)  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationContext():
return def(_that.actorId,_that.branchId,_that.projectionHash);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue? actorId, @UuidValueConverter()  UuidValue branchId,  String projectionHash)?  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationContext() when def != null:
return def(_that.actorId,_that.branchId,_that.projectionHash);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceOperationContext implements ServiceOperationContext {
   _ServiceOperationContext({@UuidValueConverter() this.actorId, @UuidValueConverter() required this.branchId, required this.projectionHash});
  factory _ServiceOperationContext.fromJson(Map<String, dynamic> json) => _$ServiceOperationContextFromJson(json);

@override@UuidValueConverter() final  UuidValue? actorId;
@override@UuidValueConverter() final  UuidValue branchId;
@override final  String projectionHash;

/// Create a copy of ServiceOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceOperationContextCopyWith<_ServiceOperationContext> get copyWith => __$ServiceOperationContextCopyWithImpl<_ServiceOperationContext>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceOperationContextToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceOperationContext&&(identical(other.actorId, actorId) || other.actorId == actorId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,actorId,branchId,projectionHash);

@override
String toString() {
  return 'ServiceOperationContext.def(actorId: $actorId, branchId: $branchId, projectionHash: $projectionHash)';
}


}

/// @nodoc
abstract mixin class _$ServiceOperationContextCopyWith<$Res> implements $ServiceOperationContextCopyWith<$Res> {
  factory _$ServiceOperationContextCopyWith(_ServiceOperationContext value, $Res Function(_ServiceOperationContext) _then) = __$ServiceOperationContextCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue? actorId,@UuidValueConverter() UuidValue branchId, String projectionHash
});




}
/// @nodoc
class __$ServiceOperationContextCopyWithImpl<$Res>
    implements _$ServiceOperationContextCopyWith<$Res> {
  __$ServiceOperationContextCopyWithImpl(this._self, this._then);

  final _ServiceOperationContext _self;
  final $Res Function(_ServiceOperationContext) _then;

/// Create a copy of ServiceOperationContext
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? actorId = freezed,Object? branchId = null,Object? projectionHash = null,}) {
  return _then(_ServiceOperationContext(
actorId: freezed == actorId ? _self.actorId : actorId // ignore: cast_nullable_to_non_nullable
as UuidValue?,branchId: null == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue,projectionHash: null == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String,
  ));
}


}


/// @nodoc
mixin _$ServiceOperationEconomicReceiptRefsV1 {

 String get contractVersion;@UuidValueConverter() UuidValue get serviceOperationId;@UuidValueConverter() UuidValue get serviceContractId;@UuidValueConverter() UuidValue get permitId;@UuidValueConverter() UuidValue get priceId;@UuidValueConverter() UuidValue get priceScheduleId;@UuidValueConverter() UuidValue get rateSnapshotId;@UuidValueConverter() UuidValue get priceReservationId;@UuidValueConverter() UuidValue get smartContractReservationId;@UuidValueConverter() UuidValue get settlementId;@UuidValueConverter() UuidValue? get transactionId;@UuidValueConverter() UuidValue get payerWalletBalanceId;@UuidValueConverter() UuidValue get receiverWalletBalanceId; String get status; bool get idempotentReplay;
/// Create a copy of ServiceOperationEconomicReceiptRefsV1
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceOperationEconomicReceiptRefsV1CopyWith<ServiceOperationEconomicReceiptRefsV1> get copyWith => _$ServiceOperationEconomicReceiptRefsV1CopyWithImpl<ServiceOperationEconomicReceiptRefsV1>(this as ServiceOperationEconomicReceiptRefsV1, _$identity);

  /// Serializes this ServiceOperationEconomicReceiptRefsV1 to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceOperationEconomicReceiptRefsV1&&(identical(other.contractVersion, contractVersion) || other.contractVersion == contractVersion)&&(identical(other.serviceOperationId, serviceOperationId) || other.serviceOperationId == serviceOperationId)&&(identical(other.serviceContractId, serviceContractId) || other.serviceContractId == serviceContractId)&&(identical(other.permitId, permitId) || other.permitId == permitId)&&(identical(other.priceId, priceId) || other.priceId == priceId)&&(identical(other.priceScheduleId, priceScheduleId) || other.priceScheduleId == priceScheduleId)&&(identical(other.rateSnapshotId, rateSnapshotId) || other.rateSnapshotId == rateSnapshotId)&&(identical(other.priceReservationId, priceReservationId) || other.priceReservationId == priceReservationId)&&(identical(other.smartContractReservationId, smartContractReservationId) || other.smartContractReservationId == smartContractReservationId)&&(identical(other.settlementId, settlementId) || other.settlementId == settlementId)&&(identical(other.transactionId, transactionId) || other.transactionId == transactionId)&&(identical(other.payerWalletBalanceId, payerWalletBalanceId) || other.payerWalletBalanceId == payerWalletBalanceId)&&(identical(other.receiverWalletBalanceId, receiverWalletBalanceId) || other.receiverWalletBalanceId == receiverWalletBalanceId)&&(identical(other.status, status) || other.status == status)&&(identical(other.idempotentReplay, idempotentReplay) || other.idempotentReplay == idempotentReplay));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contractVersion,serviceOperationId,serviceContractId,permitId,priceId,priceScheduleId,rateSnapshotId,priceReservationId,smartContractReservationId,settlementId,transactionId,payerWalletBalanceId,receiverWalletBalanceId,status,idempotentReplay);

@override
String toString() {
  return 'ServiceOperationEconomicReceiptRefsV1(contractVersion: $contractVersion, serviceOperationId: $serviceOperationId, serviceContractId: $serviceContractId, permitId: $permitId, priceId: $priceId, priceScheduleId: $priceScheduleId, rateSnapshotId: $rateSnapshotId, priceReservationId: $priceReservationId, smartContractReservationId: $smartContractReservationId, settlementId: $settlementId, transactionId: $transactionId, payerWalletBalanceId: $payerWalletBalanceId, receiverWalletBalanceId: $receiverWalletBalanceId, status: $status, idempotentReplay: $idempotentReplay)';
}


}

/// @nodoc
abstract mixin class $ServiceOperationEconomicReceiptRefsV1CopyWith<$Res>  {
  factory $ServiceOperationEconomicReceiptRefsV1CopyWith(ServiceOperationEconomicReceiptRefsV1 value, $Res Function(ServiceOperationEconomicReceiptRefsV1) _then) = _$ServiceOperationEconomicReceiptRefsV1CopyWithImpl;
@useResult
$Res call({
 String contractVersion,@UuidValueConverter() UuidValue serviceOperationId,@UuidValueConverter() UuidValue serviceContractId,@UuidValueConverter() UuidValue permitId,@UuidValueConverter() UuidValue priceId,@UuidValueConverter() UuidValue priceScheduleId,@UuidValueConverter() UuidValue rateSnapshotId,@UuidValueConverter() UuidValue priceReservationId,@UuidValueConverter() UuidValue smartContractReservationId,@UuidValueConverter() UuidValue settlementId,@UuidValueConverter() UuidValue? transactionId,@UuidValueConverter() UuidValue payerWalletBalanceId,@UuidValueConverter() UuidValue receiverWalletBalanceId, String status, bool idempotentReplay
});




}
/// @nodoc
class _$ServiceOperationEconomicReceiptRefsV1CopyWithImpl<$Res>
    implements $ServiceOperationEconomicReceiptRefsV1CopyWith<$Res> {
  _$ServiceOperationEconomicReceiptRefsV1CopyWithImpl(this._self, this._then);

  final ServiceOperationEconomicReceiptRefsV1 _self;
  final $Res Function(ServiceOperationEconomicReceiptRefsV1) _then;

/// Create a copy of ServiceOperationEconomicReceiptRefsV1
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? contractVersion = null,Object? serviceOperationId = null,Object? serviceContractId = null,Object? permitId = null,Object? priceId = null,Object? priceScheduleId = null,Object? rateSnapshotId = null,Object? priceReservationId = null,Object? smartContractReservationId = null,Object? settlementId = null,Object? transactionId = freezed,Object? payerWalletBalanceId = null,Object? receiverWalletBalanceId = null,Object? status = null,Object? idempotentReplay = null,}) {
  return _then(_self.copyWith(
contractVersion: null == contractVersion ? _self.contractVersion : contractVersion // ignore: cast_nullable_to_non_nullable
as String,serviceOperationId: null == serviceOperationId ? _self.serviceOperationId : serviceOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceContractId: null == serviceContractId ? _self.serviceContractId : serviceContractId // ignore: cast_nullable_to_non_nullable
as UuidValue,permitId: null == permitId ? _self.permitId : permitId // ignore: cast_nullable_to_non_nullable
as UuidValue,priceId: null == priceId ? _self.priceId : priceId // ignore: cast_nullable_to_non_nullable
as UuidValue,priceScheduleId: null == priceScheduleId ? _self.priceScheduleId : priceScheduleId // ignore: cast_nullable_to_non_nullable
as UuidValue,rateSnapshotId: null == rateSnapshotId ? _self.rateSnapshotId : rateSnapshotId // ignore: cast_nullable_to_non_nullable
as UuidValue,priceReservationId: null == priceReservationId ? _self.priceReservationId : priceReservationId // ignore: cast_nullable_to_non_nullable
as UuidValue,smartContractReservationId: null == smartContractReservationId ? _self.smartContractReservationId : smartContractReservationId // ignore: cast_nullable_to_non_nullable
as UuidValue,settlementId: null == settlementId ? _self.settlementId : settlementId // ignore: cast_nullable_to_non_nullable
as UuidValue,transactionId: freezed == transactionId ? _self.transactionId : transactionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,payerWalletBalanceId: null == payerWalletBalanceId ? _self.payerWalletBalanceId : payerWalletBalanceId // ignore: cast_nullable_to_non_nullable
as UuidValue,receiverWalletBalanceId: null == receiverWalletBalanceId ? _self.receiverWalletBalanceId : receiverWalletBalanceId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,idempotentReplay: null == idempotentReplay ? _self.idempotentReplay : idempotentReplay // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}

}


/// Adds pattern-matching-related methods to [ServiceOperationEconomicReceiptRefsV1].
extension ServiceOperationEconomicReceiptRefsV1Patterns on ServiceOperationEconomicReceiptRefsV1 {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceOperationEconomicReceiptRefsV1 value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceOperationEconomicReceiptRefsV1() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceOperationEconomicReceiptRefsV1 value)  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationEconomicReceiptRefsV1():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceOperationEconomicReceiptRefsV1 value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationEconomicReceiptRefsV1() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String contractVersion, @UuidValueConverter()  UuidValue serviceOperationId, @UuidValueConverter()  UuidValue serviceContractId, @UuidValueConverter()  UuidValue permitId, @UuidValueConverter()  UuidValue priceId, @UuidValueConverter()  UuidValue priceScheduleId, @UuidValueConverter()  UuidValue rateSnapshotId, @UuidValueConverter()  UuidValue priceReservationId, @UuidValueConverter()  UuidValue smartContractReservationId, @UuidValueConverter()  UuidValue settlementId, @UuidValueConverter()  UuidValue? transactionId, @UuidValueConverter()  UuidValue payerWalletBalanceId, @UuidValueConverter()  UuidValue receiverWalletBalanceId,  String status,  bool idempotentReplay)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceOperationEconomicReceiptRefsV1() when def != null:
return def(_that.contractVersion,_that.serviceOperationId,_that.serviceContractId,_that.permitId,_that.priceId,_that.priceScheduleId,_that.rateSnapshotId,_that.priceReservationId,_that.smartContractReservationId,_that.settlementId,_that.transactionId,_that.payerWalletBalanceId,_that.receiverWalletBalanceId,_that.status,_that.idempotentReplay);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String contractVersion, @UuidValueConverter()  UuidValue serviceOperationId, @UuidValueConverter()  UuidValue serviceContractId, @UuidValueConverter()  UuidValue permitId, @UuidValueConverter()  UuidValue priceId, @UuidValueConverter()  UuidValue priceScheduleId, @UuidValueConverter()  UuidValue rateSnapshotId, @UuidValueConverter()  UuidValue priceReservationId, @UuidValueConverter()  UuidValue smartContractReservationId, @UuidValueConverter()  UuidValue settlementId, @UuidValueConverter()  UuidValue? transactionId, @UuidValueConverter()  UuidValue payerWalletBalanceId, @UuidValueConverter()  UuidValue receiverWalletBalanceId,  String status,  bool idempotentReplay)  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationEconomicReceiptRefsV1():
return def(_that.contractVersion,_that.serviceOperationId,_that.serviceContractId,_that.permitId,_that.priceId,_that.priceScheduleId,_that.rateSnapshotId,_that.priceReservationId,_that.smartContractReservationId,_that.settlementId,_that.transactionId,_that.payerWalletBalanceId,_that.receiverWalletBalanceId,_that.status,_that.idempotentReplay);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String contractVersion, @UuidValueConverter()  UuidValue serviceOperationId, @UuidValueConverter()  UuidValue serviceContractId, @UuidValueConverter()  UuidValue permitId, @UuidValueConverter()  UuidValue priceId, @UuidValueConverter()  UuidValue priceScheduleId, @UuidValueConverter()  UuidValue rateSnapshotId, @UuidValueConverter()  UuidValue priceReservationId, @UuidValueConverter()  UuidValue smartContractReservationId, @UuidValueConverter()  UuidValue settlementId, @UuidValueConverter()  UuidValue? transactionId, @UuidValueConverter()  UuidValue payerWalletBalanceId, @UuidValueConverter()  UuidValue receiverWalletBalanceId,  String status,  bool idempotentReplay)?  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationEconomicReceiptRefsV1() when def != null:
return def(_that.contractVersion,_that.serviceOperationId,_that.serviceContractId,_that.permitId,_that.priceId,_that.priceScheduleId,_that.rateSnapshotId,_that.priceReservationId,_that.smartContractReservationId,_that.settlementId,_that.transactionId,_that.payerWalletBalanceId,_that.receiverWalletBalanceId,_that.status,_that.idempotentReplay);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceOperationEconomicReceiptRefsV1 implements ServiceOperationEconomicReceiptRefsV1 {
   _ServiceOperationEconomicReceiptRefsV1({required this.contractVersion, @UuidValueConverter() required this.serviceOperationId, @UuidValueConverter() required this.serviceContractId, @UuidValueConverter() required this.permitId, @UuidValueConverter() required this.priceId, @UuidValueConverter() required this.priceScheduleId, @UuidValueConverter() required this.rateSnapshotId, @UuidValueConverter() required this.priceReservationId, @UuidValueConverter() required this.smartContractReservationId, @UuidValueConverter() required this.settlementId, @UuidValueConverter() this.transactionId, @UuidValueConverter() required this.payerWalletBalanceId, @UuidValueConverter() required this.receiverWalletBalanceId, required this.status, required this.idempotentReplay});
  factory _ServiceOperationEconomicReceiptRefsV1.fromJson(Map<String, dynamic> json) => _$ServiceOperationEconomicReceiptRefsV1FromJson(json);

@override final  String contractVersion;
@override@UuidValueConverter() final  UuidValue serviceOperationId;
@override@UuidValueConverter() final  UuidValue serviceContractId;
@override@UuidValueConverter() final  UuidValue permitId;
@override@UuidValueConverter() final  UuidValue priceId;
@override@UuidValueConverter() final  UuidValue priceScheduleId;
@override@UuidValueConverter() final  UuidValue rateSnapshotId;
@override@UuidValueConverter() final  UuidValue priceReservationId;
@override@UuidValueConverter() final  UuidValue smartContractReservationId;
@override@UuidValueConverter() final  UuidValue settlementId;
@override@UuidValueConverter() final  UuidValue? transactionId;
@override@UuidValueConverter() final  UuidValue payerWalletBalanceId;
@override@UuidValueConverter() final  UuidValue receiverWalletBalanceId;
@override final  String status;
@override final  bool idempotentReplay;

/// Create a copy of ServiceOperationEconomicReceiptRefsV1
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceOperationEconomicReceiptRefsV1CopyWith<_ServiceOperationEconomicReceiptRefsV1> get copyWith => __$ServiceOperationEconomicReceiptRefsV1CopyWithImpl<_ServiceOperationEconomicReceiptRefsV1>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceOperationEconomicReceiptRefsV1ToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceOperationEconomicReceiptRefsV1&&(identical(other.contractVersion, contractVersion) || other.contractVersion == contractVersion)&&(identical(other.serviceOperationId, serviceOperationId) || other.serviceOperationId == serviceOperationId)&&(identical(other.serviceContractId, serviceContractId) || other.serviceContractId == serviceContractId)&&(identical(other.permitId, permitId) || other.permitId == permitId)&&(identical(other.priceId, priceId) || other.priceId == priceId)&&(identical(other.priceScheduleId, priceScheduleId) || other.priceScheduleId == priceScheduleId)&&(identical(other.rateSnapshotId, rateSnapshotId) || other.rateSnapshotId == rateSnapshotId)&&(identical(other.priceReservationId, priceReservationId) || other.priceReservationId == priceReservationId)&&(identical(other.smartContractReservationId, smartContractReservationId) || other.smartContractReservationId == smartContractReservationId)&&(identical(other.settlementId, settlementId) || other.settlementId == settlementId)&&(identical(other.transactionId, transactionId) || other.transactionId == transactionId)&&(identical(other.payerWalletBalanceId, payerWalletBalanceId) || other.payerWalletBalanceId == payerWalletBalanceId)&&(identical(other.receiverWalletBalanceId, receiverWalletBalanceId) || other.receiverWalletBalanceId == receiverWalletBalanceId)&&(identical(other.status, status) || other.status == status)&&(identical(other.idempotentReplay, idempotentReplay) || other.idempotentReplay == idempotentReplay));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,contractVersion,serviceOperationId,serviceContractId,permitId,priceId,priceScheduleId,rateSnapshotId,priceReservationId,smartContractReservationId,settlementId,transactionId,payerWalletBalanceId,receiverWalletBalanceId,status,idempotentReplay);

@override
String toString() {
  return 'ServiceOperationEconomicReceiptRefsV1.def(contractVersion: $contractVersion, serviceOperationId: $serviceOperationId, serviceContractId: $serviceContractId, permitId: $permitId, priceId: $priceId, priceScheduleId: $priceScheduleId, rateSnapshotId: $rateSnapshotId, priceReservationId: $priceReservationId, smartContractReservationId: $smartContractReservationId, settlementId: $settlementId, transactionId: $transactionId, payerWalletBalanceId: $payerWalletBalanceId, receiverWalletBalanceId: $receiverWalletBalanceId, status: $status, idempotentReplay: $idempotentReplay)';
}


}

/// @nodoc
abstract mixin class _$ServiceOperationEconomicReceiptRefsV1CopyWith<$Res> implements $ServiceOperationEconomicReceiptRefsV1CopyWith<$Res> {
  factory _$ServiceOperationEconomicReceiptRefsV1CopyWith(_ServiceOperationEconomicReceiptRefsV1 value, $Res Function(_ServiceOperationEconomicReceiptRefsV1) _then) = __$ServiceOperationEconomicReceiptRefsV1CopyWithImpl;
@override @useResult
$Res call({
 String contractVersion,@UuidValueConverter() UuidValue serviceOperationId,@UuidValueConverter() UuidValue serviceContractId,@UuidValueConverter() UuidValue permitId,@UuidValueConverter() UuidValue priceId,@UuidValueConverter() UuidValue priceScheduleId,@UuidValueConverter() UuidValue rateSnapshotId,@UuidValueConverter() UuidValue priceReservationId,@UuidValueConverter() UuidValue smartContractReservationId,@UuidValueConverter() UuidValue settlementId,@UuidValueConverter() UuidValue? transactionId,@UuidValueConverter() UuidValue payerWalletBalanceId,@UuidValueConverter() UuidValue receiverWalletBalanceId, String status, bool idempotentReplay
});




}
/// @nodoc
class __$ServiceOperationEconomicReceiptRefsV1CopyWithImpl<$Res>
    implements _$ServiceOperationEconomicReceiptRefsV1CopyWith<$Res> {
  __$ServiceOperationEconomicReceiptRefsV1CopyWithImpl(this._self, this._then);

  final _ServiceOperationEconomicReceiptRefsV1 _self;
  final $Res Function(_ServiceOperationEconomicReceiptRefsV1) _then;

/// Create a copy of ServiceOperationEconomicReceiptRefsV1
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? contractVersion = null,Object? serviceOperationId = null,Object? serviceContractId = null,Object? permitId = null,Object? priceId = null,Object? priceScheduleId = null,Object? rateSnapshotId = null,Object? priceReservationId = null,Object? smartContractReservationId = null,Object? settlementId = null,Object? transactionId = freezed,Object? payerWalletBalanceId = null,Object? receiverWalletBalanceId = null,Object? status = null,Object? idempotentReplay = null,}) {
  return _then(_ServiceOperationEconomicReceiptRefsV1(
contractVersion: null == contractVersion ? _self.contractVersion : contractVersion // ignore: cast_nullable_to_non_nullable
as String,serviceOperationId: null == serviceOperationId ? _self.serviceOperationId : serviceOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue,serviceContractId: null == serviceContractId ? _self.serviceContractId : serviceContractId // ignore: cast_nullable_to_non_nullable
as UuidValue,permitId: null == permitId ? _self.permitId : permitId // ignore: cast_nullable_to_non_nullable
as UuidValue,priceId: null == priceId ? _self.priceId : priceId // ignore: cast_nullable_to_non_nullable
as UuidValue,priceScheduleId: null == priceScheduleId ? _self.priceScheduleId : priceScheduleId // ignore: cast_nullable_to_non_nullable
as UuidValue,rateSnapshotId: null == rateSnapshotId ? _self.rateSnapshotId : rateSnapshotId // ignore: cast_nullable_to_non_nullable
as UuidValue,priceReservationId: null == priceReservationId ? _self.priceReservationId : priceReservationId // ignore: cast_nullable_to_non_nullable
as UuidValue,smartContractReservationId: null == smartContractReservationId ? _self.smartContractReservationId : smartContractReservationId // ignore: cast_nullable_to_non_nullable
as UuidValue,settlementId: null == settlementId ? _self.settlementId : settlementId // ignore: cast_nullable_to_non_nullable
as UuidValue,transactionId: freezed == transactionId ? _self.transactionId : transactionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,payerWalletBalanceId: null == payerWalletBalanceId ? _self.payerWalletBalanceId : payerWalletBalanceId // ignore: cast_nullable_to_non_nullable
as UuidValue,receiverWalletBalanceId: null == receiverWalletBalanceId ? _self.receiverWalletBalanceId : receiverWalletBalanceId // ignore: cast_nullable_to_non_nullable
as UuidValue,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as String,idempotentReplay: null == idempotentReplay ? _self.idempotentReplay : idempotentReplay // ignore: cast_nullable_to_non_nullable
as bool,
  ));
}


}


/// @nodoc
mixin _$ServiceOperation {

 ServiceOperationRequest? get request; ServiceOperationResponse? get response;
/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceOperationCopyWith<ServiceOperation> get copyWith => _$ServiceOperationCopyWithImpl<ServiceOperation>(this as ServiceOperation, _$identity);

  /// Serializes this ServiceOperation to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response);

@override
String toString() {
  return 'ServiceOperation(request: $request, response: $response)';
}


}

/// @nodoc
abstract mixin class $ServiceOperationCopyWith<$Res>  {
  factory $ServiceOperationCopyWith(ServiceOperation value, $Res Function(ServiceOperation) _then) = _$ServiceOperationCopyWithImpl;
@useResult
$Res call({
 ServiceOperationRequest? request, ServiceOperationResponse? response
});


$ServiceOperationRequestCopyWith<$Res>? get request;$ServiceOperationResponseCopyWith<$Res>? get response;

}
/// @nodoc
class _$ServiceOperationCopyWithImpl<$Res>
    implements $ServiceOperationCopyWith<$Res> {
  _$ServiceOperationCopyWithImpl(this._self, this._then);

  final ServiceOperation _self;
  final $Res Function(ServiceOperation) _then;

/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? request = freezed,Object? response = freezed,}) {
  return _then(_self.copyWith(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as ServiceOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as ServiceOperationResponse?,
  ));
}
/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $ServiceOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $ServiceOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}
}


/// Adds pattern-matching-related methods to [ServiceOperation].
extension ServiceOperationPatterns on ServiceOperation {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceOperation value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceOperation() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceOperation value)  def,}){
final _that = this;
switch (_that) {
case _ServiceOperation():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceOperation value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceOperation() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( ServiceOperationRequest? request,  ServiceOperationResponse? response)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceOperation() when def != null:
return def(_that.request,_that.response);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( ServiceOperationRequest? request,  ServiceOperationResponse? response)  def,}) {final _that = this;
switch (_that) {
case _ServiceOperation():
return def(_that.request,_that.response);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( ServiceOperationRequest? request,  ServiceOperationResponse? response)?  def,}) {final _that = this;
switch (_that) {
case _ServiceOperation() when def != null:
return def(_that.request,_that.response);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceOperation implements ServiceOperation {
   _ServiceOperation({this.request, this.response});
  factory _ServiceOperation.fromJson(Map<String, dynamic> json) => _$ServiceOperationFromJson(json);

@override final  ServiceOperationRequest? request;
@override final  ServiceOperationResponse? response;

/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceOperationCopyWith<_ServiceOperation> get copyWith => __$ServiceOperationCopyWithImpl<_ServiceOperation>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceOperationToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceOperation&&(identical(other.request, request) || other.request == request)&&(identical(other.response, response) || other.response == response));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,request,response);

@override
String toString() {
  return 'ServiceOperation.def(request: $request, response: $response)';
}


}

/// @nodoc
abstract mixin class _$ServiceOperationCopyWith<$Res> implements $ServiceOperationCopyWith<$Res> {
  factory _$ServiceOperationCopyWith(_ServiceOperation value, $Res Function(_ServiceOperation) _then) = __$ServiceOperationCopyWithImpl;
@override @useResult
$Res call({
 ServiceOperationRequest? request, ServiceOperationResponse? response
});


@override $ServiceOperationRequestCopyWith<$Res>? get request;@override $ServiceOperationResponseCopyWith<$Res>? get response;

}
/// @nodoc
class __$ServiceOperationCopyWithImpl<$Res>
    implements _$ServiceOperationCopyWith<$Res> {
  __$ServiceOperationCopyWithImpl(this._self, this._then);

  final _ServiceOperation _self;
  final $Res Function(_ServiceOperation) _then;

/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? request = freezed,Object? response = freezed,}) {
  return _then(_ServiceOperation(
request: freezed == request ? _self.request : request // ignore: cast_nullable_to_non_nullable
as ServiceOperationRequest?,response: freezed == response ? _self.response : response // ignore: cast_nullable_to_non_nullable
as ServiceOperationResponse?,
  ));
}

/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationRequestCopyWith<$Res>? get request {
    if (_self.request == null) {
    return null;
  }

  return $ServiceOperationRequestCopyWith<$Res>(_self.request!, (value) {
    return _then(_self.copyWith(request: value));
  });
}/// Create a copy of ServiceOperation
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationResponseCopyWith<$Res>? get response {
    if (_self.response == null) {
    return null;
  }

  return $ServiceOperationResponseCopyWith<$Res>(_self.response!, (value) {
    return _then(_self.copyWith(response: value));
  });
}
}


/// @nodoc
mixin _$ServiceApiDispatchEnvelope {

@UuidValueConverter() UuidValue get apiCallId;@UuidValueConverter() UuidValue get apiCapabilityEndpointId;@UuidValueConverter() UuidValue get callKey; String get requestHash;@UuidValueConverter() UuidValue get commitId;@UuidValueConverter() UuidValue get headCommitId;@UuidValueConverter() UuidValue get branchId; String get projectionHash; String get apiName; String get capabilityName; String get endpointName; String get endpointRef; String get discriminant; String get sourcePath;@UuidValueConverter() UuidValue get requestModelId;@UuidValueConverter() UuidValue get requestClassConfigId; String get requestClassRef; String get requestSourcePath; String? get responseClassRef; String? get responseSourcePath;
/// Create a copy of ServiceApiDispatchEnvelope
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceApiDispatchEnvelopeCopyWith<ServiceApiDispatchEnvelope> get copyWith => _$ServiceApiDispatchEnvelopeCopyWithImpl<ServiceApiDispatchEnvelope>(this as ServiceApiDispatchEnvelope, _$identity);

  /// Serializes this ServiceApiDispatchEnvelope to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceApiDispatchEnvelope&&(identical(other.apiCallId, apiCallId) || other.apiCallId == apiCallId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.callKey, callKey) || other.callKey == callKey)&&(identical(other.requestHash, requestHash) || other.requestHash == requestHash)&&(identical(other.commitId, commitId) || other.commitId == commitId)&&(identical(other.headCommitId, headCommitId) || other.headCommitId == headCommitId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.apiName, apiName) || other.apiName == apiName)&&(identical(other.capabilityName, capabilityName) || other.capabilityName == capabilityName)&&(identical(other.endpointName, endpointName) || other.endpointName == endpointName)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.sourcePath, sourcePath) || other.sourcePath == sourcePath)&&(identical(other.requestModelId, requestModelId) || other.requestModelId == requestModelId)&&(identical(other.requestClassConfigId, requestClassConfigId) || other.requestClassConfigId == requestClassConfigId)&&(identical(other.requestClassRef, requestClassRef) || other.requestClassRef == requestClassRef)&&(identical(other.requestSourcePath, requestSourcePath) || other.requestSourcePath == requestSourcePath)&&(identical(other.responseClassRef, responseClassRef) || other.responseClassRef == responseClassRef)&&(identical(other.responseSourcePath, responseSourcePath) || other.responseSourcePath == responseSourcePath));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,apiCallId,apiCapabilityEndpointId,callKey,requestHash,commitId,headCommitId,branchId,projectionHash,apiName,capabilityName,endpointName,endpointRef,discriminant,sourcePath,requestModelId,requestClassConfigId,requestClassRef,requestSourcePath,responseClassRef,responseSourcePath]);

@override
String toString() {
  return 'ServiceApiDispatchEnvelope(apiCallId: $apiCallId, apiCapabilityEndpointId: $apiCapabilityEndpointId, callKey: $callKey, requestHash: $requestHash, commitId: $commitId, headCommitId: $headCommitId, branchId: $branchId, projectionHash: $projectionHash, apiName: $apiName, capabilityName: $capabilityName, endpointName: $endpointName, endpointRef: $endpointRef, discriminant: $discriminant, sourcePath: $sourcePath, requestModelId: $requestModelId, requestClassConfigId: $requestClassConfigId, requestClassRef: $requestClassRef, requestSourcePath: $requestSourcePath, responseClassRef: $responseClassRef, responseSourcePath: $responseSourcePath)';
}


}

/// @nodoc
abstract mixin class $ServiceApiDispatchEnvelopeCopyWith<$Res>  {
  factory $ServiceApiDispatchEnvelopeCopyWith(ServiceApiDispatchEnvelope value, $Res Function(ServiceApiDispatchEnvelope) _then) = _$ServiceApiDispatchEnvelopeCopyWithImpl;
@useResult
$Res call({
@UuidValueConverter() UuidValue apiCallId,@UuidValueConverter() UuidValue apiCapabilityEndpointId,@UuidValueConverter() UuidValue callKey, String requestHash,@UuidValueConverter() UuidValue commitId,@UuidValueConverter() UuidValue headCommitId,@UuidValueConverter() UuidValue branchId, String projectionHash, String apiName, String capabilityName, String endpointName, String endpointRef, String discriminant, String sourcePath,@UuidValueConverter() UuidValue requestModelId,@UuidValueConverter() UuidValue requestClassConfigId, String requestClassRef, String requestSourcePath, String? responseClassRef, String? responseSourcePath
});




}
/// @nodoc
class _$ServiceApiDispatchEnvelopeCopyWithImpl<$Res>
    implements $ServiceApiDispatchEnvelopeCopyWith<$Res> {
  _$ServiceApiDispatchEnvelopeCopyWithImpl(this._self, this._then);

  final ServiceApiDispatchEnvelope _self;
  final $Res Function(ServiceApiDispatchEnvelope) _then;

/// Create a copy of ServiceApiDispatchEnvelope
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? apiCallId = null,Object? apiCapabilityEndpointId = null,Object? callKey = null,Object? requestHash = null,Object? commitId = null,Object? headCommitId = null,Object? branchId = null,Object? projectionHash = null,Object? apiName = null,Object? capabilityName = null,Object? endpointName = null,Object? endpointRef = null,Object? discriminant = null,Object? sourcePath = null,Object? requestModelId = null,Object? requestClassConfigId = null,Object? requestClassRef = null,Object? requestSourcePath = null,Object? responseClassRef = freezed,Object? responseSourcePath = freezed,}) {
  return _then(_self.copyWith(
apiCallId: null == apiCallId ? _self.apiCallId : apiCallId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpointId: null == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue,callKey: null == callKey ? _self.callKey : callKey // ignore: cast_nullable_to_non_nullable
as UuidValue,requestHash: null == requestHash ? _self.requestHash : requestHash // ignore: cast_nullable_to_non_nullable
as String,commitId: null == commitId ? _self.commitId : commitId // ignore: cast_nullable_to_non_nullable
as UuidValue,headCommitId: null == headCommitId ? _self.headCommitId : headCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,branchId: null == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue,projectionHash: null == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String,apiName: null == apiName ? _self.apiName : apiName // ignore: cast_nullable_to_non_nullable
as String,capabilityName: null == capabilityName ? _self.capabilityName : capabilityName // ignore: cast_nullable_to_non_nullable
as String,endpointName: null == endpointName ? _self.endpointName : endpointName // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,sourcePath: null == sourcePath ? _self.sourcePath : sourcePath // ignore: cast_nullable_to_non_nullable
as String,requestModelId: null == requestModelId ? _self.requestModelId : requestModelId // ignore: cast_nullable_to_non_nullable
as UuidValue,requestClassConfigId: null == requestClassConfigId ? _self.requestClassConfigId : requestClassConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,requestClassRef: null == requestClassRef ? _self.requestClassRef : requestClassRef // ignore: cast_nullable_to_non_nullable
as String,requestSourcePath: null == requestSourcePath ? _self.requestSourcePath : requestSourcePath // ignore: cast_nullable_to_non_nullable
as String,responseClassRef: freezed == responseClassRef ? _self.responseClassRef : responseClassRef // ignore: cast_nullable_to_non_nullable
as String?,responseSourcePath: freezed == responseSourcePath ? _self.responseSourcePath : responseSourcePath // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [ServiceApiDispatchEnvelope].
extension ServiceApiDispatchEnvelopePatterns on ServiceApiDispatchEnvelope {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceApiDispatchEnvelope value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchEnvelope() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceApiDispatchEnvelope value)  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchEnvelope():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceApiDispatchEnvelope value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchEnvelope() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@UuidValueConverter()  UuidValue apiCallId, @UuidValueConverter()  UuidValue apiCapabilityEndpointId, @UuidValueConverter()  UuidValue callKey,  String requestHash, @UuidValueConverter()  UuidValue commitId, @UuidValueConverter()  UuidValue headCommitId, @UuidValueConverter()  UuidValue branchId,  String projectionHash,  String apiName,  String capabilityName,  String endpointName,  String endpointRef,  String discriminant,  String sourcePath, @UuidValueConverter()  UuidValue requestModelId, @UuidValueConverter()  UuidValue requestClassConfigId,  String requestClassRef,  String requestSourcePath,  String? responseClassRef,  String? responseSourcePath)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchEnvelope() when def != null:
return def(_that.apiCallId,_that.apiCapabilityEndpointId,_that.callKey,_that.requestHash,_that.commitId,_that.headCommitId,_that.branchId,_that.projectionHash,_that.apiName,_that.capabilityName,_that.endpointName,_that.endpointRef,_that.discriminant,_that.sourcePath,_that.requestModelId,_that.requestClassConfigId,_that.requestClassRef,_that.requestSourcePath,_that.responseClassRef,_that.responseSourcePath);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@UuidValueConverter()  UuidValue apiCallId, @UuidValueConverter()  UuidValue apiCapabilityEndpointId, @UuidValueConverter()  UuidValue callKey,  String requestHash, @UuidValueConverter()  UuidValue commitId, @UuidValueConverter()  UuidValue headCommitId, @UuidValueConverter()  UuidValue branchId,  String projectionHash,  String apiName,  String capabilityName,  String endpointName,  String endpointRef,  String discriminant,  String sourcePath, @UuidValueConverter()  UuidValue requestModelId, @UuidValueConverter()  UuidValue requestClassConfigId,  String requestClassRef,  String requestSourcePath,  String? responseClassRef,  String? responseSourcePath)  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchEnvelope():
return def(_that.apiCallId,_that.apiCapabilityEndpointId,_that.callKey,_that.requestHash,_that.commitId,_that.headCommitId,_that.branchId,_that.projectionHash,_that.apiName,_that.capabilityName,_that.endpointName,_that.endpointRef,_that.discriminant,_that.sourcePath,_that.requestModelId,_that.requestClassConfigId,_that.requestClassRef,_that.requestSourcePath,_that.responseClassRef,_that.responseSourcePath);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@UuidValueConverter()  UuidValue apiCallId, @UuidValueConverter()  UuidValue apiCapabilityEndpointId, @UuidValueConverter()  UuidValue callKey,  String requestHash, @UuidValueConverter()  UuidValue commitId, @UuidValueConverter()  UuidValue headCommitId, @UuidValueConverter()  UuidValue branchId,  String projectionHash,  String apiName,  String capabilityName,  String endpointName,  String endpointRef,  String discriminant,  String sourcePath, @UuidValueConverter()  UuidValue requestModelId, @UuidValueConverter()  UuidValue requestClassConfigId,  String requestClassRef,  String requestSourcePath,  String? responseClassRef,  String? responseSourcePath)?  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchEnvelope() when def != null:
return def(_that.apiCallId,_that.apiCapabilityEndpointId,_that.callKey,_that.requestHash,_that.commitId,_that.headCommitId,_that.branchId,_that.projectionHash,_that.apiName,_that.capabilityName,_that.endpointName,_that.endpointRef,_that.discriminant,_that.sourcePath,_that.requestModelId,_that.requestClassConfigId,_that.requestClassRef,_that.requestSourcePath,_that.responseClassRef,_that.responseSourcePath);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceApiDispatchEnvelope implements ServiceApiDispatchEnvelope {
   _ServiceApiDispatchEnvelope({@UuidValueConverter() required this.apiCallId, @UuidValueConverter() required this.apiCapabilityEndpointId, @UuidValueConverter() required this.callKey, required this.requestHash, @UuidValueConverter() required this.commitId, @UuidValueConverter() required this.headCommitId, @UuidValueConverter() required this.branchId, required this.projectionHash, required this.apiName, required this.capabilityName, required this.endpointName, required this.endpointRef, required this.discriminant, required this.sourcePath, @UuidValueConverter() required this.requestModelId, @UuidValueConverter() required this.requestClassConfigId, required this.requestClassRef, required this.requestSourcePath, this.responseClassRef, this.responseSourcePath});
  factory _ServiceApiDispatchEnvelope.fromJson(Map<String, dynamic> json) => _$ServiceApiDispatchEnvelopeFromJson(json);

@override@UuidValueConverter() final  UuidValue apiCallId;
@override@UuidValueConverter() final  UuidValue apiCapabilityEndpointId;
@override@UuidValueConverter() final  UuidValue callKey;
@override final  String requestHash;
@override@UuidValueConverter() final  UuidValue commitId;
@override@UuidValueConverter() final  UuidValue headCommitId;
@override@UuidValueConverter() final  UuidValue branchId;
@override final  String projectionHash;
@override final  String apiName;
@override final  String capabilityName;
@override final  String endpointName;
@override final  String endpointRef;
@override final  String discriminant;
@override final  String sourcePath;
@override@UuidValueConverter() final  UuidValue requestModelId;
@override@UuidValueConverter() final  UuidValue requestClassConfigId;
@override final  String requestClassRef;
@override final  String requestSourcePath;
@override final  String? responseClassRef;
@override final  String? responseSourcePath;

/// Create a copy of ServiceApiDispatchEnvelope
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceApiDispatchEnvelopeCopyWith<_ServiceApiDispatchEnvelope> get copyWith => __$ServiceApiDispatchEnvelopeCopyWithImpl<_ServiceApiDispatchEnvelope>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceApiDispatchEnvelopeToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceApiDispatchEnvelope&&(identical(other.apiCallId, apiCallId) || other.apiCallId == apiCallId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.callKey, callKey) || other.callKey == callKey)&&(identical(other.requestHash, requestHash) || other.requestHash == requestHash)&&(identical(other.commitId, commitId) || other.commitId == commitId)&&(identical(other.headCommitId, headCommitId) || other.headCommitId == headCommitId)&&(identical(other.branchId, branchId) || other.branchId == branchId)&&(identical(other.projectionHash, projectionHash) || other.projectionHash == projectionHash)&&(identical(other.apiName, apiName) || other.apiName == apiName)&&(identical(other.capabilityName, capabilityName) || other.capabilityName == capabilityName)&&(identical(other.endpointName, endpointName) || other.endpointName == endpointName)&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.sourcePath, sourcePath) || other.sourcePath == sourcePath)&&(identical(other.requestModelId, requestModelId) || other.requestModelId == requestModelId)&&(identical(other.requestClassConfigId, requestClassConfigId) || other.requestClassConfigId == requestClassConfigId)&&(identical(other.requestClassRef, requestClassRef) || other.requestClassRef == requestClassRef)&&(identical(other.requestSourcePath, requestSourcePath) || other.requestSourcePath == requestSourcePath)&&(identical(other.responseClassRef, responseClassRef) || other.responseClassRef == responseClassRef)&&(identical(other.responseSourcePath, responseSourcePath) || other.responseSourcePath == responseSourcePath));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,apiCallId,apiCapabilityEndpointId,callKey,requestHash,commitId,headCommitId,branchId,projectionHash,apiName,capabilityName,endpointName,endpointRef,discriminant,sourcePath,requestModelId,requestClassConfigId,requestClassRef,requestSourcePath,responseClassRef,responseSourcePath]);

@override
String toString() {
  return 'ServiceApiDispatchEnvelope.def(apiCallId: $apiCallId, apiCapabilityEndpointId: $apiCapabilityEndpointId, callKey: $callKey, requestHash: $requestHash, commitId: $commitId, headCommitId: $headCommitId, branchId: $branchId, projectionHash: $projectionHash, apiName: $apiName, capabilityName: $capabilityName, endpointName: $endpointName, endpointRef: $endpointRef, discriminant: $discriminant, sourcePath: $sourcePath, requestModelId: $requestModelId, requestClassConfigId: $requestClassConfigId, requestClassRef: $requestClassRef, requestSourcePath: $requestSourcePath, responseClassRef: $responseClassRef, responseSourcePath: $responseSourcePath)';
}


}

/// @nodoc
abstract mixin class _$ServiceApiDispatchEnvelopeCopyWith<$Res> implements $ServiceApiDispatchEnvelopeCopyWith<$Res> {
  factory _$ServiceApiDispatchEnvelopeCopyWith(_ServiceApiDispatchEnvelope value, $Res Function(_ServiceApiDispatchEnvelope) _then) = __$ServiceApiDispatchEnvelopeCopyWithImpl;
@override @useResult
$Res call({
@UuidValueConverter() UuidValue apiCallId,@UuidValueConverter() UuidValue apiCapabilityEndpointId,@UuidValueConverter() UuidValue callKey, String requestHash,@UuidValueConverter() UuidValue commitId,@UuidValueConverter() UuidValue headCommitId,@UuidValueConverter() UuidValue branchId, String projectionHash, String apiName, String capabilityName, String endpointName, String endpointRef, String discriminant, String sourcePath,@UuidValueConverter() UuidValue requestModelId,@UuidValueConverter() UuidValue requestClassConfigId, String requestClassRef, String requestSourcePath, String? responseClassRef, String? responseSourcePath
});




}
/// @nodoc
class __$ServiceApiDispatchEnvelopeCopyWithImpl<$Res>
    implements _$ServiceApiDispatchEnvelopeCopyWith<$Res> {
  __$ServiceApiDispatchEnvelopeCopyWithImpl(this._self, this._then);

  final _ServiceApiDispatchEnvelope _self;
  final $Res Function(_ServiceApiDispatchEnvelope) _then;

/// Create a copy of ServiceApiDispatchEnvelope
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? apiCallId = null,Object? apiCapabilityEndpointId = null,Object? callKey = null,Object? requestHash = null,Object? commitId = null,Object? headCommitId = null,Object? branchId = null,Object? projectionHash = null,Object? apiName = null,Object? capabilityName = null,Object? endpointName = null,Object? endpointRef = null,Object? discriminant = null,Object? sourcePath = null,Object? requestModelId = null,Object? requestClassConfigId = null,Object? requestClassRef = null,Object? requestSourcePath = null,Object? responseClassRef = freezed,Object? responseSourcePath = freezed,}) {
  return _then(_ServiceApiDispatchEnvelope(
apiCallId: null == apiCallId ? _self.apiCallId : apiCallId // ignore: cast_nullable_to_non_nullable
as UuidValue,apiCapabilityEndpointId: null == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue,callKey: null == callKey ? _self.callKey : callKey // ignore: cast_nullable_to_non_nullable
as UuidValue,requestHash: null == requestHash ? _self.requestHash : requestHash // ignore: cast_nullable_to_non_nullable
as String,commitId: null == commitId ? _self.commitId : commitId // ignore: cast_nullable_to_non_nullable
as UuidValue,headCommitId: null == headCommitId ? _self.headCommitId : headCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue,branchId: null == branchId ? _self.branchId : branchId // ignore: cast_nullable_to_non_nullable
as UuidValue,projectionHash: null == projectionHash ? _self.projectionHash : projectionHash // ignore: cast_nullable_to_non_nullable
as String,apiName: null == apiName ? _self.apiName : apiName // ignore: cast_nullable_to_non_nullable
as String,capabilityName: null == capabilityName ? _self.capabilityName : capabilityName // ignore: cast_nullable_to_non_nullable
as String,endpointName: null == endpointName ? _self.endpointName : endpointName // ignore: cast_nullable_to_non_nullable
as String,endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,sourcePath: null == sourcePath ? _self.sourcePath : sourcePath // ignore: cast_nullable_to_non_nullable
as String,requestModelId: null == requestModelId ? _self.requestModelId : requestModelId // ignore: cast_nullable_to_non_nullable
as UuidValue,requestClassConfigId: null == requestClassConfigId ? _self.requestClassConfigId : requestClassConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue,requestClassRef: null == requestClassRef ? _self.requestClassRef : requestClassRef // ignore: cast_nullable_to_non_nullable
as String,requestSourcePath: null == requestSourcePath ? _self.requestSourcePath : requestSourcePath // ignore: cast_nullable_to_non_nullable
as String,responseClassRef: freezed == responseClassRef ? _self.responseClassRef : responseClassRef // ignore: cast_nullable_to_non_nullable
as String?,responseSourcePath: freezed == responseSourcePath ? _self.responseSourcePath : responseSourcePath // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}


/// @nodoc
mixin _$ServiceApiDispatchFulfillmentBinding {

 String get name; String get graphTarget; String get graphCapabilityFunctionName; String get graphFunctionPythonRef; String get graphFunctionRuntimeTarget; String get methodName; String get requestTypeRef; String get responseTypeRef; String get sourcePath;@UuidValueConverter() UuidValue? get apiCapabilityEndpointFunctionId;
/// Create a copy of ServiceApiDispatchFulfillmentBinding
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceApiDispatchFulfillmentBindingCopyWith<ServiceApiDispatchFulfillmentBinding> get copyWith => _$ServiceApiDispatchFulfillmentBindingCopyWithImpl<ServiceApiDispatchFulfillmentBinding>(this as ServiceApiDispatchFulfillmentBinding, _$identity);

  /// Serializes this ServiceApiDispatchFulfillmentBinding to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceApiDispatchFulfillmentBinding&&(identical(other.name, name) || other.name == name)&&(identical(other.graphTarget, graphTarget) || other.graphTarget == graphTarget)&&(identical(other.graphCapabilityFunctionName, graphCapabilityFunctionName) || other.graphCapabilityFunctionName == graphCapabilityFunctionName)&&(identical(other.graphFunctionPythonRef, graphFunctionPythonRef) || other.graphFunctionPythonRef == graphFunctionPythonRef)&&(identical(other.graphFunctionRuntimeTarget, graphFunctionRuntimeTarget) || other.graphFunctionRuntimeTarget == graphFunctionRuntimeTarget)&&(identical(other.methodName, methodName) || other.methodName == methodName)&&(identical(other.requestTypeRef, requestTypeRef) || other.requestTypeRef == requestTypeRef)&&(identical(other.responseTypeRef, responseTypeRef) || other.responseTypeRef == responseTypeRef)&&(identical(other.sourcePath, sourcePath) || other.sourcePath == sourcePath)&&(identical(other.apiCapabilityEndpointFunctionId, apiCapabilityEndpointFunctionId) || other.apiCapabilityEndpointFunctionId == apiCapabilityEndpointFunctionId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,name,graphTarget,graphCapabilityFunctionName,graphFunctionPythonRef,graphFunctionRuntimeTarget,methodName,requestTypeRef,responseTypeRef,sourcePath,apiCapabilityEndpointFunctionId);

@override
String toString() {
  return 'ServiceApiDispatchFulfillmentBinding(name: $name, graphTarget: $graphTarget, graphCapabilityFunctionName: $graphCapabilityFunctionName, graphFunctionPythonRef: $graphFunctionPythonRef, graphFunctionRuntimeTarget: $graphFunctionRuntimeTarget, methodName: $methodName, requestTypeRef: $requestTypeRef, responseTypeRef: $responseTypeRef, sourcePath: $sourcePath, apiCapabilityEndpointFunctionId: $apiCapabilityEndpointFunctionId)';
}


}

/// @nodoc
abstract mixin class $ServiceApiDispatchFulfillmentBindingCopyWith<$Res>  {
  factory $ServiceApiDispatchFulfillmentBindingCopyWith(ServiceApiDispatchFulfillmentBinding value, $Res Function(ServiceApiDispatchFulfillmentBinding) _then) = _$ServiceApiDispatchFulfillmentBindingCopyWithImpl;
@useResult
$Res call({
 String name, String graphTarget, String graphCapabilityFunctionName, String graphFunctionPythonRef, String graphFunctionRuntimeTarget, String methodName, String requestTypeRef, String responseTypeRef, String sourcePath,@UuidValueConverter() UuidValue? apiCapabilityEndpointFunctionId
});




}
/// @nodoc
class _$ServiceApiDispatchFulfillmentBindingCopyWithImpl<$Res>
    implements $ServiceApiDispatchFulfillmentBindingCopyWith<$Res> {
  _$ServiceApiDispatchFulfillmentBindingCopyWithImpl(this._self, this._then);

  final ServiceApiDispatchFulfillmentBinding _self;
  final $Res Function(ServiceApiDispatchFulfillmentBinding) _then;

/// Create a copy of ServiceApiDispatchFulfillmentBinding
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? name = null,Object? graphTarget = null,Object? graphCapabilityFunctionName = null,Object? graphFunctionPythonRef = null,Object? graphFunctionRuntimeTarget = null,Object? methodName = null,Object? requestTypeRef = null,Object? responseTypeRef = null,Object? sourcePath = null,Object? apiCapabilityEndpointFunctionId = freezed,}) {
  return _then(_self.copyWith(
name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,graphTarget: null == graphTarget ? _self.graphTarget : graphTarget // ignore: cast_nullable_to_non_nullable
as String,graphCapabilityFunctionName: null == graphCapabilityFunctionName ? _self.graphCapabilityFunctionName : graphCapabilityFunctionName // ignore: cast_nullable_to_non_nullable
as String,graphFunctionPythonRef: null == graphFunctionPythonRef ? _self.graphFunctionPythonRef : graphFunctionPythonRef // ignore: cast_nullable_to_non_nullable
as String,graphFunctionRuntimeTarget: null == graphFunctionRuntimeTarget ? _self.graphFunctionRuntimeTarget : graphFunctionRuntimeTarget // ignore: cast_nullable_to_non_nullable
as String,methodName: null == methodName ? _self.methodName : methodName // ignore: cast_nullable_to_non_nullable
as String,requestTypeRef: null == requestTypeRef ? _self.requestTypeRef : requestTypeRef // ignore: cast_nullable_to_non_nullable
as String,responseTypeRef: null == responseTypeRef ? _self.responseTypeRef : responseTypeRef // ignore: cast_nullable_to_non_nullable
as String,sourcePath: null == sourcePath ? _self.sourcePath : sourcePath // ignore: cast_nullable_to_non_nullable
as String,apiCapabilityEndpointFunctionId: freezed == apiCapabilityEndpointFunctionId ? _self.apiCapabilityEndpointFunctionId : apiCapabilityEndpointFunctionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

}


/// Adds pattern-matching-related methods to [ServiceApiDispatchFulfillmentBinding].
extension ServiceApiDispatchFulfillmentBindingPatterns on ServiceApiDispatchFulfillmentBinding {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceApiDispatchFulfillmentBinding value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchFulfillmentBinding() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceApiDispatchFulfillmentBinding value)  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchFulfillmentBinding():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceApiDispatchFulfillmentBinding value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchFulfillmentBinding() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String name,  String graphTarget,  String graphCapabilityFunctionName,  String graphFunctionPythonRef,  String graphFunctionRuntimeTarget,  String methodName,  String requestTypeRef,  String responseTypeRef,  String sourcePath, @UuidValueConverter()  UuidValue? apiCapabilityEndpointFunctionId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchFulfillmentBinding() when def != null:
return def(_that.name,_that.graphTarget,_that.graphCapabilityFunctionName,_that.graphFunctionPythonRef,_that.graphFunctionRuntimeTarget,_that.methodName,_that.requestTypeRef,_that.responseTypeRef,_that.sourcePath,_that.apiCapabilityEndpointFunctionId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String name,  String graphTarget,  String graphCapabilityFunctionName,  String graphFunctionPythonRef,  String graphFunctionRuntimeTarget,  String methodName,  String requestTypeRef,  String responseTypeRef,  String sourcePath, @UuidValueConverter()  UuidValue? apiCapabilityEndpointFunctionId)  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchFulfillmentBinding():
return def(_that.name,_that.graphTarget,_that.graphCapabilityFunctionName,_that.graphFunctionPythonRef,_that.graphFunctionRuntimeTarget,_that.methodName,_that.requestTypeRef,_that.responseTypeRef,_that.sourcePath,_that.apiCapabilityEndpointFunctionId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String name,  String graphTarget,  String graphCapabilityFunctionName,  String graphFunctionPythonRef,  String graphFunctionRuntimeTarget,  String methodName,  String requestTypeRef,  String responseTypeRef,  String sourcePath, @UuidValueConverter()  UuidValue? apiCapabilityEndpointFunctionId)?  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchFulfillmentBinding() when def != null:
return def(_that.name,_that.graphTarget,_that.graphCapabilityFunctionName,_that.graphFunctionPythonRef,_that.graphFunctionRuntimeTarget,_that.methodName,_that.requestTypeRef,_that.responseTypeRef,_that.sourcePath,_that.apiCapabilityEndpointFunctionId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceApiDispatchFulfillmentBinding implements ServiceApiDispatchFulfillmentBinding {
   _ServiceApiDispatchFulfillmentBinding({required this.name, required this.graphTarget, required this.graphCapabilityFunctionName, required this.graphFunctionPythonRef, required this.graphFunctionRuntimeTarget, required this.methodName, required this.requestTypeRef, required this.responseTypeRef, required this.sourcePath, @UuidValueConverter() this.apiCapabilityEndpointFunctionId});
  factory _ServiceApiDispatchFulfillmentBinding.fromJson(Map<String, dynamic> json) => _$ServiceApiDispatchFulfillmentBindingFromJson(json);

@override final  String name;
@override final  String graphTarget;
@override final  String graphCapabilityFunctionName;
@override final  String graphFunctionPythonRef;
@override final  String graphFunctionRuntimeTarget;
@override final  String methodName;
@override final  String requestTypeRef;
@override final  String responseTypeRef;
@override final  String sourcePath;
@override@UuidValueConverter() final  UuidValue? apiCapabilityEndpointFunctionId;

/// Create a copy of ServiceApiDispatchFulfillmentBinding
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceApiDispatchFulfillmentBindingCopyWith<_ServiceApiDispatchFulfillmentBinding> get copyWith => __$ServiceApiDispatchFulfillmentBindingCopyWithImpl<_ServiceApiDispatchFulfillmentBinding>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceApiDispatchFulfillmentBindingToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceApiDispatchFulfillmentBinding&&(identical(other.name, name) || other.name == name)&&(identical(other.graphTarget, graphTarget) || other.graphTarget == graphTarget)&&(identical(other.graphCapabilityFunctionName, graphCapabilityFunctionName) || other.graphCapabilityFunctionName == graphCapabilityFunctionName)&&(identical(other.graphFunctionPythonRef, graphFunctionPythonRef) || other.graphFunctionPythonRef == graphFunctionPythonRef)&&(identical(other.graphFunctionRuntimeTarget, graphFunctionRuntimeTarget) || other.graphFunctionRuntimeTarget == graphFunctionRuntimeTarget)&&(identical(other.methodName, methodName) || other.methodName == methodName)&&(identical(other.requestTypeRef, requestTypeRef) || other.requestTypeRef == requestTypeRef)&&(identical(other.responseTypeRef, responseTypeRef) || other.responseTypeRef == responseTypeRef)&&(identical(other.sourcePath, sourcePath) || other.sourcePath == sourcePath)&&(identical(other.apiCapabilityEndpointFunctionId, apiCapabilityEndpointFunctionId) || other.apiCapabilityEndpointFunctionId == apiCapabilityEndpointFunctionId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,name,graphTarget,graphCapabilityFunctionName,graphFunctionPythonRef,graphFunctionRuntimeTarget,methodName,requestTypeRef,responseTypeRef,sourcePath,apiCapabilityEndpointFunctionId);

@override
String toString() {
  return 'ServiceApiDispatchFulfillmentBinding.def(name: $name, graphTarget: $graphTarget, graphCapabilityFunctionName: $graphCapabilityFunctionName, graphFunctionPythonRef: $graphFunctionPythonRef, graphFunctionRuntimeTarget: $graphFunctionRuntimeTarget, methodName: $methodName, requestTypeRef: $requestTypeRef, responseTypeRef: $responseTypeRef, sourcePath: $sourcePath, apiCapabilityEndpointFunctionId: $apiCapabilityEndpointFunctionId)';
}


}

/// @nodoc
abstract mixin class _$ServiceApiDispatchFulfillmentBindingCopyWith<$Res> implements $ServiceApiDispatchFulfillmentBindingCopyWith<$Res> {
  factory _$ServiceApiDispatchFulfillmentBindingCopyWith(_ServiceApiDispatchFulfillmentBinding value, $Res Function(_ServiceApiDispatchFulfillmentBinding) _then) = __$ServiceApiDispatchFulfillmentBindingCopyWithImpl;
@override @useResult
$Res call({
 String name, String graphTarget, String graphCapabilityFunctionName, String graphFunctionPythonRef, String graphFunctionRuntimeTarget, String methodName, String requestTypeRef, String responseTypeRef, String sourcePath,@UuidValueConverter() UuidValue? apiCapabilityEndpointFunctionId
});




}
/// @nodoc
class __$ServiceApiDispatchFulfillmentBindingCopyWithImpl<$Res>
    implements _$ServiceApiDispatchFulfillmentBindingCopyWith<$Res> {
  __$ServiceApiDispatchFulfillmentBindingCopyWithImpl(this._self, this._then);

  final _ServiceApiDispatchFulfillmentBinding _self;
  final $Res Function(_ServiceApiDispatchFulfillmentBinding) _then;

/// Create a copy of ServiceApiDispatchFulfillmentBinding
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? name = null,Object? graphTarget = null,Object? graphCapabilityFunctionName = null,Object? graphFunctionPythonRef = null,Object? graphFunctionRuntimeTarget = null,Object? methodName = null,Object? requestTypeRef = null,Object? responseTypeRef = null,Object? sourcePath = null,Object? apiCapabilityEndpointFunctionId = freezed,}) {
  return _then(_ServiceApiDispatchFulfillmentBinding(
name: null == name ? _self.name : name // ignore: cast_nullable_to_non_nullable
as String,graphTarget: null == graphTarget ? _self.graphTarget : graphTarget // ignore: cast_nullable_to_non_nullable
as String,graphCapabilityFunctionName: null == graphCapabilityFunctionName ? _self.graphCapabilityFunctionName : graphCapabilityFunctionName // ignore: cast_nullable_to_non_nullable
as String,graphFunctionPythonRef: null == graphFunctionPythonRef ? _self.graphFunctionPythonRef : graphFunctionPythonRef // ignore: cast_nullable_to_non_nullable
as String,graphFunctionRuntimeTarget: null == graphFunctionRuntimeTarget ? _self.graphFunctionRuntimeTarget : graphFunctionRuntimeTarget // ignore: cast_nullable_to_non_nullable
as String,methodName: null == methodName ? _self.methodName : methodName // ignore: cast_nullable_to_non_nullable
as String,requestTypeRef: null == requestTypeRef ? _self.requestTypeRef : requestTypeRef // ignore: cast_nullable_to_non_nullable
as String,responseTypeRef: null == responseTypeRef ? _self.responseTypeRef : responseTypeRef // ignore: cast_nullable_to_non_nullable
as String,sourcePath: null == sourcePath ? _self.sourcePath : sourcePath // ignore: cast_nullable_to_non_nullable
as String,apiCapabilityEndpointFunctionId: freezed == apiCapabilityEndpointFunctionId ? _self.apiCapabilityEndpointFunctionId : apiCapabilityEndpointFunctionId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}


}


/// @nodoc
mixin _$ServiceApiDispatchRequest {

 String get operationKey; ServiceApiDispatchEnvelope get envelope; Map<String, dynamic> get requestPayload; List<ServiceApiDispatchFulfillmentBinding> get fulfillmentBindings;
/// Create a copy of ServiceApiDispatchRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceApiDispatchRequestCopyWith<ServiceApiDispatchRequest> get copyWith => _$ServiceApiDispatchRequestCopyWithImpl<ServiceApiDispatchRequest>(this as ServiceApiDispatchRequest, _$identity);

  /// Serializes this ServiceApiDispatchRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceApiDispatchRequest&&(identical(other.operationKey, operationKey) || other.operationKey == operationKey)&&(identical(other.envelope, envelope) || other.envelope == envelope)&&const DeepCollectionEquality().equals(other.requestPayload, requestPayload)&&const DeepCollectionEquality().equals(other.fulfillmentBindings, fulfillmentBindings));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operationKey,envelope,const DeepCollectionEquality().hash(requestPayload),const DeepCollectionEquality().hash(fulfillmentBindings));

@override
String toString() {
  return 'ServiceApiDispatchRequest(operationKey: $operationKey, envelope: $envelope, requestPayload: $requestPayload, fulfillmentBindings: $fulfillmentBindings)';
}


}

/// @nodoc
abstract mixin class $ServiceApiDispatchRequestCopyWith<$Res>  {
  factory $ServiceApiDispatchRequestCopyWith(ServiceApiDispatchRequest value, $Res Function(ServiceApiDispatchRequest) _then) = _$ServiceApiDispatchRequestCopyWithImpl;
@useResult
$Res call({
 String operationKey, ServiceApiDispatchEnvelope envelope, Map<String, dynamic> requestPayload, List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings
});


$ServiceApiDispatchEnvelopeCopyWith<$Res> get envelope;

}
/// @nodoc
class _$ServiceApiDispatchRequestCopyWithImpl<$Res>
    implements $ServiceApiDispatchRequestCopyWith<$Res> {
  _$ServiceApiDispatchRequestCopyWithImpl(this._self, this._then);

  final ServiceApiDispatchRequest _self;
  final $Res Function(ServiceApiDispatchRequest) _then;

/// Create a copy of ServiceApiDispatchRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? operationKey = null,Object? envelope = null,Object? requestPayload = null,Object? fulfillmentBindings = null,}) {
  return _then(_self.copyWith(
operationKey: null == operationKey ? _self.operationKey : operationKey // ignore: cast_nullable_to_non_nullable
as String,envelope: null == envelope ? _self.envelope : envelope // ignore: cast_nullable_to_non_nullable
as ServiceApiDispatchEnvelope,requestPayload: null == requestPayload ? _self.requestPayload : requestPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,fulfillmentBindings: null == fulfillmentBindings ? _self.fulfillmentBindings : fulfillmentBindings // ignore: cast_nullable_to_non_nullable
as List<ServiceApiDispatchFulfillmentBinding>,
  ));
}
/// Create a copy of ServiceApiDispatchRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceApiDispatchEnvelopeCopyWith<$Res> get envelope {
  
  return $ServiceApiDispatchEnvelopeCopyWith<$Res>(_self.envelope, (value) {
    return _then(_self.copyWith(envelope: value));
  });
}
}


/// Adds pattern-matching-related methods to [ServiceApiDispatchRequest].
extension ServiceApiDispatchRequestPatterns on ServiceApiDispatchRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceApiDispatchRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceApiDispatchRequest value)  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceApiDispatchRequest value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String operationKey,  ServiceApiDispatchEnvelope envelope,  Map<String, dynamic> requestPayload,  List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchRequest() when def != null:
return def(_that.operationKey,_that.envelope,_that.requestPayload,_that.fulfillmentBindings);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String operationKey,  ServiceApiDispatchEnvelope envelope,  Map<String, dynamic> requestPayload,  List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings)  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchRequest():
return def(_that.operationKey,_that.envelope,_that.requestPayload,_that.fulfillmentBindings);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String operationKey,  ServiceApiDispatchEnvelope envelope,  Map<String, dynamic> requestPayload,  List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings)?  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchRequest() when def != null:
return def(_that.operationKey,_that.envelope,_that.requestPayload,_that.fulfillmentBindings);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceApiDispatchRequest implements ServiceApiDispatchRequest {
   _ServiceApiDispatchRequest({required this.operationKey, required this.envelope, required final  Map<String, dynamic> requestPayload, final  List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings = const []}): _requestPayload = requestPayload,_fulfillmentBindings = fulfillmentBindings;
  factory _ServiceApiDispatchRequest.fromJson(Map<String, dynamic> json) => _$ServiceApiDispatchRequestFromJson(json);

@override final  String operationKey;
@override final  ServiceApiDispatchEnvelope envelope;
 final  Map<String, dynamic> _requestPayload;
@override Map<String, dynamic> get requestPayload {
  if (_requestPayload is EqualUnmodifiableMapView) return _requestPayload;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_requestPayload);
}

 final  List<ServiceApiDispatchFulfillmentBinding> _fulfillmentBindings;
@override@JsonKey() List<ServiceApiDispatchFulfillmentBinding> get fulfillmentBindings {
  if (_fulfillmentBindings is EqualUnmodifiableListView) return _fulfillmentBindings;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableListView(_fulfillmentBindings);
}


/// Create a copy of ServiceApiDispatchRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceApiDispatchRequestCopyWith<_ServiceApiDispatchRequest> get copyWith => __$ServiceApiDispatchRequestCopyWithImpl<_ServiceApiDispatchRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceApiDispatchRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceApiDispatchRequest&&(identical(other.operationKey, operationKey) || other.operationKey == operationKey)&&(identical(other.envelope, envelope) || other.envelope == envelope)&&const DeepCollectionEquality().equals(other._requestPayload, _requestPayload)&&const DeepCollectionEquality().equals(other._fulfillmentBindings, _fulfillmentBindings));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,operationKey,envelope,const DeepCollectionEquality().hash(_requestPayload),const DeepCollectionEquality().hash(_fulfillmentBindings));

@override
String toString() {
  return 'ServiceApiDispatchRequest.def(operationKey: $operationKey, envelope: $envelope, requestPayload: $requestPayload, fulfillmentBindings: $fulfillmentBindings)';
}


}

/// @nodoc
abstract mixin class _$ServiceApiDispatchRequestCopyWith<$Res> implements $ServiceApiDispatchRequestCopyWith<$Res> {
  factory _$ServiceApiDispatchRequestCopyWith(_ServiceApiDispatchRequest value, $Res Function(_ServiceApiDispatchRequest) _then) = __$ServiceApiDispatchRequestCopyWithImpl;
@override @useResult
$Res call({
 String operationKey, ServiceApiDispatchEnvelope envelope, Map<String, dynamic> requestPayload, List<ServiceApiDispatchFulfillmentBinding> fulfillmentBindings
});


@override $ServiceApiDispatchEnvelopeCopyWith<$Res> get envelope;

}
/// @nodoc
class __$ServiceApiDispatchRequestCopyWithImpl<$Res>
    implements _$ServiceApiDispatchRequestCopyWith<$Res> {
  __$ServiceApiDispatchRequestCopyWithImpl(this._self, this._then);

  final _ServiceApiDispatchRequest _self;
  final $Res Function(_ServiceApiDispatchRequest) _then;

/// Create a copy of ServiceApiDispatchRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? operationKey = null,Object? envelope = null,Object? requestPayload = null,Object? fulfillmentBindings = null,}) {
  return _then(_ServiceApiDispatchRequest(
operationKey: null == operationKey ? _self.operationKey : operationKey // ignore: cast_nullable_to_non_nullable
as String,envelope: null == envelope ? _self.envelope : envelope // ignore: cast_nullable_to_non_nullable
as ServiceApiDispatchEnvelope,requestPayload: null == requestPayload ? _self._requestPayload : requestPayload // ignore: cast_nullable_to_non_nullable
as Map<String, dynamic>,fulfillmentBindings: null == fulfillmentBindings ? _self._fulfillmentBindings : fulfillmentBindings // ignore: cast_nullable_to_non_nullable
as List<ServiceApiDispatchFulfillmentBinding>,
  ));
}

/// Create a copy of ServiceApiDispatchRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceApiDispatchEnvelopeCopyWith<$Res> get envelope {
  
  return $ServiceApiDispatchEnvelopeCopyWith<$Res>(_self.envelope, (value) {
    return _then(_self.copyWith(envelope: value));
  });
}
}


/// @nodoc
mixin _$ServiceApiDispatchReceipt {

 String get endpointRef; String get discriminant;@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) RequestStatus get status;@UuidValueConverter() UuidValue? get networkRequestId;@UuidValueConverter() UuidValue? get apiCallId;@UuidValueConverter() UuidValue? get apiCapabilityEndpointId;@UuidValueConverter() UuidValue? get callKey; String? get requestHash;@UuidValueConverter() UuidValue? get requestModelId;@UuidValueConverter() UuidValue? get apiCallOutcomeId;@UuidValueConverter() UuidValue? get responseModelId;@UuidValueConverter() UuidValue? get serviceOperationId;@UuidValueConverter() UuidValue? get serviceOperationConfigId;@UuidValueConverter() UuidValue? get serviceOperationConfigApiEndpointId;@UuidValueConverter() UuidValue? get serviceOperationCommitId;@UuidValueConverter() UuidValue? get serviceOperationHeadCommitId;@UuidValueConverter() UuidValue? get serviceOperationBranchId; String? get serviceOperationProjectionHash;@UuidValueConverter() UuidValue? get apiCallOutcomeCommitId;@UuidValueConverter() UuidValue? get apiCallOutcomeHeadCommitId;@UuidValueConverter() UuidValue? get apiCallOutcomeBranchId; String? get apiCallOutcomeProjectionHash; ServiceOperationEconomicReceiptRefsV1? get economicReceipt;
/// Create a copy of ServiceApiDispatchReceipt
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceApiDispatchReceiptCopyWith<ServiceApiDispatchReceipt> get copyWith => _$ServiceApiDispatchReceiptCopyWithImpl<ServiceApiDispatchReceipt>(this as ServiceApiDispatchReceipt, _$identity);

  /// Serializes this ServiceApiDispatchReceipt to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceApiDispatchReceipt&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.status, status) || other.status == status)&&(identical(other.networkRequestId, networkRequestId) || other.networkRequestId == networkRequestId)&&(identical(other.apiCallId, apiCallId) || other.apiCallId == apiCallId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.callKey, callKey) || other.callKey == callKey)&&(identical(other.requestHash, requestHash) || other.requestHash == requestHash)&&(identical(other.requestModelId, requestModelId) || other.requestModelId == requestModelId)&&(identical(other.apiCallOutcomeId, apiCallOutcomeId) || other.apiCallOutcomeId == apiCallOutcomeId)&&(identical(other.responseModelId, responseModelId) || other.responseModelId == responseModelId)&&(identical(other.serviceOperationId, serviceOperationId) || other.serviceOperationId == serviceOperationId)&&(identical(other.serviceOperationConfigId, serviceOperationConfigId) || other.serviceOperationConfigId == serviceOperationConfigId)&&(identical(other.serviceOperationConfigApiEndpointId, serviceOperationConfigApiEndpointId) || other.serviceOperationConfigApiEndpointId == serviceOperationConfigApiEndpointId)&&(identical(other.serviceOperationCommitId, serviceOperationCommitId) || other.serviceOperationCommitId == serviceOperationCommitId)&&(identical(other.serviceOperationHeadCommitId, serviceOperationHeadCommitId) || other.serviceOperationHeadCommitId == serviceOperationHeadCommitId)&&(identical(other.serviceOperationBranchId, serviceOperationBranchId) || other.serviceOperationBranchId == serviceOperationBranchId)&&(identical(other.serviceOperationProjectionHash, serviceOperationProjectionHash) || other.serviceOperationProjectionHash == serviceOperationProjectionHash)&&(identical(other.apiCallOutcomeCommitId, apiCallOutcomeCommitId) || other.apiCallOutcomeCommitId == apiCallOutcomeCommitId)&&(identical(other.apiCallOutcomeHeadCommitId, apiCallOutcomeHeadCommitId) || other.apiCallOutcomeHeadCommitId == apiCallOutcomeHeadCommitId)&&(identical(other.apiCallOutcomeBranchId, apiCallOutcomeBranchId) || other.apiCallOutcomeBranchId == apiCallOutcomeBranchId)&&(identical(other.apiCallOutcomeProjectionHash, apiCallOutcomeProjectionHash) || other.apiCallOutcomeProjectionHash == apiCallOutcomeProjectionHash)&&(identical(other.economicReceipt, economicReceipt) || other.economicReceipt == economicReceipt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,endpointRef,discriminant,status,networkRequestId,apiCallId,apiCapabilityEndpointId,callKey,requestHash,requestModelId,apiCallOutcomeId,responseModelId,serviceOperationId,serviceOperationConfigId,serviceOperationConfigApiEndpointId,serviceOperationCommitId,serviceOperationHeadCommitId,serviceOperationBranchId,serviceOperationProjectionHash,apiCallOutcomeCommitId,apiCallOutcomeHeadCommitId,apiCallOutcomeBranchId,apiCallOutcomeProjectionHash,economicReceipt]);

@override
String toString() {
  return 'ServiceApiDispatchReceipt(endpointRef: $endpointRef, discriminant: $discriminant, status: $status, networkRequestId: $networkRequestId, apiCallId: $apiCallId, apiCapabilityEndpointId: $apiCapabilityEndpointId, callKey: $callKey, requestHash: $requestHash, requestModelId: $requestModelId, apiCallOutcomeId: $apiCallOutcomeId, responseModelId: $responseModelId, serviceOperationId: $serviceOperationId, serviceOperationConfigId: $serviceOperationConfigId, serviceOperationConfigApiEndpointId: $serviceOperationConfigApiEndpointId, serviceOperationCommitId: $serviceOperationCommitId, serviceOperationHeadCommitId: $serviceOperationHeadCommitId, serviceOperationBranchId: $serviceOperationBranchId, serviceOperationProjectionHash: $serviceOperationProjectionHash, apiCallOutcomeCommitId: $apiCallOutcomeCommitId, apiCallOutcomeHeadCommitId: $apiCallOutcomeHeadCommitId, apiCallOutcomeBranchId: $apiCallOutcomeBranchId, apiCallOutcomeProjectionHash: $apiCallOutcomeProjectionHash, economicReceipt: $economicReceipt)';
}


}

/// @nodoc
abstract mixin class $ServiceApiDispatchReceiptCopyWith<$Res>  {
  factory $ServiceApiDispatchReceiptCopyWith(ServiceApiDispatchReceipt value, $Res Function(ServiceApiDispatchReceipt) _then) = _$ServiceApiDispatchReceiptCopyWithImpl;
@useResult
$Res call({
 String endpointRef, String discriminant,@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) RequestStatus status,@UuidValueConverter() UuidValue? networkRequestId,@UuidValueConverter() UuidValue? apiCallId,@UuidValueConverter() UuidValue? apiCapabilityEndpointId,@UuidValueConverter() UuidValue? callKey, String? requestHash,@UuidValueConverter() UuidValue? requestModelId,@UuidValueConverter() UuidValue? apiCallOutcomeId,@UuidValueConverter() UuidValue? responseModelId,@UuidValueConverter() UuidValue? serviceOperationId,@UuidValueConverter() UuidValue? serviceOperationConfigId,@UuidValueConverter() UuidValue? serviceOperationConfigApiEndpointId,@UuidValueConverter() UuidValue? serviceOperationCommitId,@UuidValueConverter() UuidValue? serviceOperationHeadCommitId,@UuidValueConverter() UuidValue? serviceOperationBranchId, String? serviceOperationProjectionHash,@UuidValueConverter() UuidValue? apiCallOutcomeCommitId,@UuidValueConverter() UuidValue? apiCallOutcomeHeadCommitId,@UuidValueConverter() UuidValue? apiCallOutcomeBranchId, String? apiCallOutcomeProjectionHash, ServiceOperationEconomicReceiptRefsV1? economicReceipt
});


$ServiceOperationEconomicReceiptRefsV1CopyWith<$Res>? get economicReceipt;

}
/// @nodoc
class _$ServiceApiDispatchReceiptCopyWithImpl<$Res>
    implements $ServiceApiDispatchReceiptCopyWith<$Res> {
  _$ServiceApiDispatchReceiptCopyWithImpl(this._self, this._then);

  final ServiceApiDispatchReceipt _self;
  final $Res Function(ServiceApiDispatchReceipt) _then;

/// Create a copy of ServiceApiDispatchReceipt
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? endpointRef = null,Object? discriminant = null,Object? status = null,Object? networkRequestId = freezed,Object? apiCallId = freezed,Object? apiCapabilityEndpointId = freezed,Object? callKey = freezed,Object? requestHash = freezed,Object? requestModelId = freezed,Object? apiCallOutcomeId = freezed,Object? responseModelId = freezed,Object? serviceOperationId = freezed,Object? serviceOperationConfigId = freezed,Object? serviceOperationConfigApiEndpointId = freezed,Object? serviceOperationCommitId = freezed,Object? serviceOperationHeadCommitId = freezed,Object? serviceOperationBranchId = freezed,Object? serviceOperationProjectionHash = freezed,Object? apiCallOutcomeCommitId = freezed,Object? apiCallOutcomeHeadCommitId = freezed,Object? apiCallOutcomeBranchId = freezed,Object? apiCallOutcomeProjectionHash = freezed,Object? economicReceipt = freezed,}) {
  return _then(_self.copyWith(
endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as RequestStatus,networkRequestId: freezed == networkRequestId ? _self.networkRequestId : networkRequestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallId: freezed == apiCallId ? _self.apiCallId : apiCallId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCapabilityEndpointId: freezed == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,callKey: freezed == callKey ? _self.callKey : callKey // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestHash: freezed == requestHash ? _self.requestHash : requestHash // ignore: cast_nullable_to_non_nullable
as String?,requestModelId: freezed == requestModelId ? _self.requestModelId : requestModelId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeId: freezed == apiCallOutcomeId ? _self.apiCallOutcomeId : apiCallOutcomeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,responseModelId: freezed == responseModelId ? _self.responseModelId : responseModelId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationId: freezed == serviceOperationId ? _self.serviceOperationId : serviceOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationConfigId: freezed == serviceOperationConfigId ? _self.serviceOperationConfigId : serviceOperationConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationConfigApiEndpointId: freezed == serviceOperationConfigApiEndpointId ? _self.serviceOperationConfigApiEndpointId : serviceOperationConfigApiEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationCommitId: freezed == serviceOperationCommitId ? _self.serviceOperationCommitId : serviceOperationCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationHeadCommitId: freezed == serviceOperationHeadCommitId ? _self.serviceOperationHeadCommitId : serviceOperationHeadCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationBranchId: freezed == serviceOperationBranchId ? _self.serviceOperationBranchId : serviceOperationBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationProjectionHash: freezed == serviceOperationProjectionHash ? _self.serviceOperationProjectionHash : serviceOperationProjectionHash // ignore: cast_nullable_to_non_nullable
as String?,apiCallOutcomeCommitId: freezed == apiCallOutcomeCommitId ? _self.apiCallOutcomeCommitId : apiCallOutcomeCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeHeadCommitId: freezed == apiCallOutcomeHeadCommitId ? _self.apiCallOutcomeHeadCommitId : apiCallOutcomeHeadCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeBranchId: freezed == apiCallOutcomeBranchId ? _self.apiCallOutcomeBranchId : apiCallOutcomeBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeProjectionHash: freezed == apiCallOutcomeProjectionHash ? _self.apiCallOutcomeProjectionHash : apiCallOutcomeProjectionHash // ignore: cast_nullable_to_non_nullable
as String?,economicReceipt: freezed == economicReceipt ? _self.economicReceipt : economicReceipt // ignore: cast_nullable_to_non_nullable
as ServiceOperationEconomicReceiptRefsV1?,
  ));
}
/// Create a copy of ServiceApiDispatchReceipt
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationEconomicReceiptRefsV1CopyWith<$Res>? get economicReceipt {
    if (_self.economicReceipt == null) {
    return null;
  }

  return $ServiceOperationEconomicReceiptRefsV1CopyWith<$Res>(_self.economicReceipt!, (value) {
    return _then(_self.copyWith(economicReceipt: value));
  });
}
}


/// Adds pattern-matching-related methods to [ServiceApiDispatchReceipt].
extension ServiceApiDispatchReceiptPatterns on ServiceApiDispatchReceipt {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceApiDispatchReceipt value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchReceipt() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceApiDispatchReceipt value)  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchReceipt():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceApiDispatchReceipt value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceApiDispatchReceipt() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( String endpointRef,  String discriminant, @JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson)  RequestStatus status, @UuidValueConverter()  UuidValue? networkRequestId, @UuidValueConverter()  UuidValue? apiCallId, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId, @UuidValueConverter()  UuidValue? callKey,  String? requestHash, @UuidValueConverter()  UuidValue? requestModelId, @UuidValueConverter()  UuidValue? apiCallOutcomeId, @UuidValueConverter()  UuidValue? responseModelId, @UuidValueConverter()  UuidValue? serviceOperationId, @UuidValueConverter()  UuidValue? serviceOperationConfigId, @UuidValueConverter()  UuidValue? serviceOperationConfigApiEndpointId, @UuidValueConverter()  UuidValue? serviceOperationCommitId, @UuidValueConverter()  UuidValue? serviceOperationHeadCommitId, @UuidValueConverter()  UuidValue? serviceOperationBranchId,  String? serviceOperationProjectionHash, @UuidValueConverter()  UuidValue? apiCallOutcomeCommitId, @UuidValueConverter()  UuidValue? apiCallOutcomeHeadCommitId, @UuidValueConverter()  UuidValue? apiCallOutcomeBranchId,  String? apiCallOutcomeProjectionHash,  ServiceOperationEconomicReceiptRefsV1? economicReceipt)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchReceipt() when def != null:
return def(_that.endpointRef,_that.discriminant,_that.status,_that.networkRequestId,_that.apiCallId,_that.apiCapabilityEndpointId,_that.callKey,_that.requestHash,_that.requestModelId,_that.apiCallOutcomeId,_that.responseModelId,_that.serviceOperationId,_that.serviceOperationConfigId,_that.serviceOperationConfigApiEndpointId,_that.serviceOperationCommitId,_that.serviceOperationHeadCommitId,_that.serviceOperationBranchId,_that.serviceOperationProjectionHash,_that.apiCallOutcomeCommitId,_that.apiCallOutcomeHeadCommitId,_that.apiCallOutcomeBranchId,_that.apiCallOutcomeProjectionHash,_that.economicReceipt);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( String endpointRef,  String discriminant, @JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson)  RequestStatus status, @UuidValueConverter()  UuidValue? networkRequestId, @UuidValueConverter()  UuidValue? apiCallId, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId, @UuidValueConverter()  UuidValue? callKey,  String? requestHash, @UuidValueConverter()  UuidValue? requestModelId, @UuidValueConverter()  UuidValue? apiCallOutcomeId, @UuidValueConverter()  UuidValue? responseModelId, @UuidValueConverter()  UuidValue? serviceOperationId, @UuidValueConverter()  UuidValue? serviceOperationConfigId, @UuidValueConverter()  UuidValue? serviceOperationConfigApiEndpointId, @UuidValueConverter()  UuidValue? serviceOperationCommitId, @UuidValueConverter()  UuidValue? serviceOperationHeadCommitId, @UuidValueConverter()  UuidValue? serviceOperationBranchId,  String? serviceOperationProjectionHash, @UuidValueConverter()  UuidValue? apiCallOutcomeCommitId, @UuidValueConverter()  UuidValue? apiCallOutcomeHeadCommitId, @UuidValueConverter()  UuidValue? apiCallOutcomeBranchId,  String? apiCallOutcomeProjectionHash,  ServiceOperationEconomicReceiptRefsV1? economicReceipt)  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchReceipt():
return def(_that.endpointRef,_that.discriminant,_that.status,_that.networkRequestId,_that.apiCallId,_that.apiCapabilityEndpointId,_that.callKey,_that.requestHash,_that.requestModelId,_that.apiCallOutcomeId,_that.responseModelId,_that.serviceOperationId,_that.serviceOperationConfigId,_that.serviceOperationConfigApiEndpointId,_that.serviceOperationCommitId,_that.serviceOperationHeadCommitId,_that.serviceOperationBranchId,_that.serviceOperationProjectionHash,_that.apiCallOutcomeCommitId,_that.apiCallOutcomeHeadCommitId,_that.apiCallOutcomeBranchId,_that.apiCallOutcomeProjectionHash,_that.economicReceipt);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( String endpointRef,  String discriminant, @JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson)  RequestStatus status, @UuidValueConverter()  UuidValue? networkRequestId, @UuidValueConverter()  UuidValue? apiCallId, @UuidValueConverter()  UuidValue? apiCapabilityEndpointId, @UuidValueConverter()  UuidValue? callKey,  String? requestHash, @UuidValueConverter()  UuidValue? requestModelId, @UuidValueConverter()  UuidValue? apiCallOutcomeId, @UuidValueConverter()  UuidValue? responseModelId, @UuidValueConverter()  UuidValue? serviceOperationId, @UuidValueConverter()  UuidValue? serviceOperationConfigId, @UuidValueConverter()  UuidValue? serviceOperationConfigApiEndpointId, @UuidValueConverter()  UuidValue? serviceOperationCommitId, @UuidValueConverter()  UuidValue? serviceOperationHeadCommitId, @UuidValueConverter()  UuidValue? serviceOperationBranchId,  String? serviceOperationProjectionHash, @UuidValueConverter()  UuidValue? apiCallOutcomeCommitId, @UuidValueConverter()  UuidValue? apiCallOutcomeHeadCommitId, @UuidValueConverter()  UuidValue? apiCallOutcomeBranchId,  String? apiCallOutcomeProjectionHash,  ServiceOperationEconomicReceiptRefsV1? economicReceipt)?  def,}) {final _that = this;
switch (_that) {
case _ServiceApiDispatchReceipt() when def != null:
return def(_that.endpointRef,_that.discriminant,_that.status,_that.networkRequestId,_that.apiCallId,_that.apiCapabilityEndpointId,_that.callKey,_that.requestHash,_that.requestModelId,_that.apiCallOutcomeId,_that.responseModelId,_that.serviceOperationId,_that.serviceOperationConfigId,_that.serviceOperationConfigApiEndpointId,_that.serviceOperationCommitId,_that.serviceOperationHeadCommitId,_that.serviceOperationBranchId,_that.serviceOperationProjectionHash,_that.apiCallOutcomeCommitId,_that.apiCallOutcomeHeadCommitId,_that.apiCallOutcomeBranchId,_that.apiCallOutcomeProjectionHash,_that.economicReceipt);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceApiDispatchReceipt implements ServiceApiDispatchReceipt {
   _ServiceApiDispatchReceipt({required this.endpointRef, required this.discriminant, @JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) required this.status, @UuidValueConverter() this.networkRequestId, @UuidValueConverter() this.apiCallId, @UuidValueConverter() this.apiCapabilityEndpointId, @UuidValueConverter() this.callKey, this.requestHash, @UuidValueConverter() this.requestModelId, @UuidValueConverter() this.apiCallOutcomeId, @UuidValueConverter() this.responseModelId, @UuidValueConverter() this.serviceOperationId, @UuidValueConverter() this.serviceOperationConfigId, @UuidValueConverter() this.serviceOperationConfigApiEndpointId, @UuidValueConverter() this.serviceOperationCommitId, @UuidValueConverter() this.serviceOperationHeadCommitId, @UuidValueConverter() this.serviceOperationBranchId, this.serviceOperationProjectionHash, @UuidValueConverter() this.apiCallOutcomeCommitId, @UuidValueConverter() this.apiCallOutcomeHeadCommitId, @UuidValueConverter() this.apiCallOutcomeBranchId, this.apiCallOutcomeProjectionHash, this.economicReceipt});
  factory _ServiceApiDispatchReceipt.fromJson(Map<String, dynamic> json) => _$ServiceApiDispatchReceiptFromJson(json);

@override final  String endpointRef;
@override final  String discriminant;
@override@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) final  RequestStatus status;
@override@UuidValueConverter() final  UuidValue? networkRequestId;
@override@UuidValueConverter() final  UuidValue? apiCallId;
@override@UuidValueConverter() final  UuidValue? apiCapabilityEndpointId;
@override@UuidValueConverter() final  UuidValue? callKey;
@override final  String? requestHash;
@override@UuidValueConverter() final  UuidValue? requestModelId;
@override@UuidValueConverter() final  UuidValue? apiCallOutcomeId;
@override@UuidValueConverter() final  UuidValue? responseModelId;
@override@UuidValueConverter() final  UuidValue? serviceOperationId;
@override@UuidValueConverter() final  UuidValue? serviceOperationConfigId;
@override@UuidValueConverter() final  UuidValue? serviceOperationConfigApiEndpointId;
@override@UuidValueConverter() final  UuidValue? serviceOperationCommitId;
@override@UuidValueConverter() final  UuidValue? serviceOperationHeadCommitId;
@override@UuidValueConverter() final  UuidValue? serviceOperationBranchId;
@override final  String? serviceOperationProjectionHash;
@override@UuidValueConverter() final  UuidValue? apiCallOutcomeCommitId;
@override@UuidValueConverter() final  UuidValue? apiCallOutcomeHeadCommitId;
@override@UuidValueConverter() final  UuidValue? apiCallOutcomeBranchId;
@override final  String? apiCallOutcomeProjectionHash;
@override final  ServiceOperationEconomicReceiptRefsV1? economicReceipt;

/// Create a copy of ServiceApiDispatchReceipt
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceApiDispatchReceiptCopyWith<_ServiceApiDispatchReceipt> get copyWith => __$ServiceApiDispatchReceiptCopyWithImpl<_ServiceApiDispatchReceipt>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceApiDispatchReceiptToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceApiDispatchReceipt&&(identical(other.endpointRef, endpointRef) || other.endpointRef == endpointRef)&&(identical(other.discriminant, discriminant) || other.discriminant == discriminant)&&(identical(other.status, status) || other.status == status)&&(identical(other.networkRequestId, networkRequestId) || other.networkRequestId == networkRequestId)&&(identical(other.apiCallId, apiCallId) || other.apiCallId == apiCallId)&&(identical(other.apiCapabilityEndpointId, apiCapabilityEndpointId) || other.apiCapabilityEndpointId == apiCapabilityEndpointId)&&(identical(other.callKey, callKey) || other.callKey == callKey)&&(identical(other.requestHash, requestHash) || other.requestHash == requestHash)&&(identical(other.requestModelId, requestModelId) || other.requestModelId == requestModelId)&&(identical(other.apiCallOutcomeId, apiCallOutcomeId) || other.apiCallOutcomeId == apiCallOutcomeId)&&(identical(other.responseModelId, responseModelId) || other.responseModelId == responseModelId)&&(identical(other.serviceOperationId, serviceOperationId) || other.serviceOperationId == serviceOperationId)&&(identical(other.serviceOperationConfigId, serviceOperationConfigId) || other.serviceOperationConfigId == serviceOperationConfigId)&&(identical(other.serviceOperationConfigApiEndpointId, serviceOperationConfigApiEndpointId) || other.serviceOperationConfigApiEndpointId == serviceOperationConfigApiEndpointId)&&(identical(other.serviceOperationCommitId, serviceOperationCommitId) || other.serviceOperationCommitId == serviceOperationCommitId)&&(identical(other.serviceOperationHeadCommitId, serviceOperationHeadCommitId) || other.serviceOperationHeadCommitId == serviceOperationHeadCommitId)&&(identical(other.serviceOperationBranchId, serviceOperationBranchId) || other.serviceOperationBranchId == serviceOperationBranchId)&&(identical(other.serviceOperationProjectionHash, serviceOperationProjectionHash) || other.serviceOperationProjectionHash == serviceOperationProjectionHash)&&(identical(other.apiCallOutcomeCommitId, apiCallOutcomeCommitId) || other.apiCallOutcomeCommitId == apiCallOutcomeCommitId)&&(identical(other.apiCallOutcomeHeadCommitId, apiCallOutcomeHeadCommitId) || other.apiCallOutcomeHeadCommitId == apiCallOutcomeHeadCommitId)&&(identical(other.apiCallOutcomeBranchId, apiCallOutcomeBranchId) || other.apiCallOutcomeBranchId == apiCallOutcomeBranchId)&&(identical(other.apiCallOutcomeProjectionHash, apiCallOutcomeProjectionHash) || other.apiCallOutcomeProjectionHash == apiCallOutcomeProjectionHash)&&(identical(other.economicReceipt, economicReceipt) || other.economicReceipt == economicReceipt));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hashAll([runtimeType,endpointRef,discriminant,status,networkRequestId,apiCallId,apiCapabilityEndpointId,callKey,requestHash,requestModelId,apiCallOutcomeId,responseModelId,serviceOperationId,serviceOperationConfigId,serviceOperationConfigApiEndpointId,serviceOperationCommitId,serviceOperationHeadCommitId,serviceOperationBranchId,serviceOperationProjectionHash,apiCallOutcomeCommitId,apiCallOutcomeHeadCommitId,apiCallOutcomeBranchId,apiCallOutcomeProjectionHash,economicReceipt]);

@override
String toString() {
  return 'ServiceApiDispatchReceipt.def(endpointRef: $endpointRef, discriminant: $discriminant, status: $status, networkRequestId: $networkRequestId, apiCallId: $apiCallId, apiCapabilityEndpointId: $apiCapabilityEndpointId, callKey: $callKey, requestHash: $requestHash, requestModelId: $requestModelId, apiCallOutcomeId: $apiCallOutcomeId, responseModelId: $responseModelId, serviceOperationId: $serviceOperationId, serviceOperationConfigId: $serviceOperationConfigId, serviceOperationConfigApiEndpointId: $serviceOperationConfigApiEndpointId, serviceOperationCommitId: $serviceOperationCommitId, serviceOperationHeadCommitId: $serviceOperationHeadCommitId, serviceOperationBranchId: $serviceOperationBranchId, serviceOperationProjectionHash: $serviceOperationProjectionHash, apiCallOutcomeCommitId: $apiCallOutcomeCommitId, apiCallOutcomeHeadCommitId: $apiCallOutcomeHeadCommitId, apiCallOutcomeBranchId: $apiCallOutcomeBranchId, apiCallOutcomeProjectionHash: $apiCallOutcomeProjectionHash, economicReceipt: $economicReceipt)';
}


}

/// @nodoc
abstract mixin class _$ServiceApiDispatchReceiptCopyWith<$Res> implements $ServiceApiDispatchReceiptCopyWith<$Res> {
  factory _$ServiceApiDispatchReceiptCopyWith(_ServiceApiDispatchReceipt value, $Res Function(_ServiceApiDispatchReceipt) _then) = __$ServiceApiDispatchReceiptCopyWithImpl;
@override @useResult
$Res call({
 String endpointRef, String discriminant,@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) RequestStatus status,@UuidValueConverter() UuidValue? networkRequestId,@UuidValueConverter() UuidValue? apiCallId,@UuidValueConverter() UuidValue? apiCapabilityEndpointId,@UuidValueConverter() UuidValue? callKey, String? requestHash,@UuidValueConverter() UuidValue? requestModelId,@UuidValueConverter() UuidValue? apiCallOutcomeId,@UuidValueConverter() UuidValue? responseModelId,@UuidValueConverter() UuidValue? serviceOperationId,@UuidValueConverter() UuidValue? serviceOperationConfigId,@UuidValueConverter() UuidValue? serviceOperationConfigApiEndpointId,@UuidValueConverter() UuidValue? serviceOperationCommitId,@UuidValueConverter() UuidValue? serviceOperationHeadCommitId,@UuidValueConverter() UuidValue? serviceOperationBranchId, String? serviceOperationProjectionHash,@UuidValueConverter() UuidValue? apiCallOutcomeCommitId,@UuidValueConverter() UuidValue? apiCallOutcomeHeadCommitId,@UuidValueConverter() UuidValue? apiCallOutcomeBranchId, String? apiCallOutcomeProjectionHash, ServiceOperationEconomicReceiptRefsV1? economicReceipt
});


@override $ServiceOperationEconomicReceiptRefsV1CopyWith<$Res>? get economicReceipt;

}
/// @nodoc
class __$ServiceApiDispatchReceiptCopyWithImpl<$Res>
    implements _$ServiceApiDispatchReceiptCopyWith<$Res> {
  __$ServiceApiDispatchReceiptCopyWithImpl(this._self, this._then);

  final _ServiceApiDispatchReceipt _self;
  final $Res Function(_ServiceApiDispatchReceipt) _then;

/// Create a copy of ServiceApiDispatchReceipt
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? endpointRef = null,Object? discriminant = null,Object? status = null,Object? networkRequestId = freezed,Object? apiCallId = freezed,Object? apiCapabilityEndpointId = freezed,Object? callKey = freezed,Object? requestHash = freezed,Object? requestModelId = freezed,Object? apiCallOutcomeId = freezed,Object? responseModelId = freezed,Object? serviceOperationId = freezed,Object? serviceOperationConfigId = freezed,Object? serviceOperationConfigApiEndpointId = freezed,Object? serviceOperationCommitId = freezed,Object? serviceOperationHeadCommitId = freezed,Object? serviceOperationBranchId = freezed,Object? serviceOperationProjectionHash = freezed,Object? apiCallOutcomeCommitId = freezed,Object? apiCallOutcomeHeadCommitId = freezed,Object? apiCallOutcomeBranchId = freezed,Object? apiCallOutcomeProjectionHash = freezed,Object? economicReceipt = freezed,}) {
  return _then(_ServiceApiDispatchReceipt(
endpointRef: null == endpointRef ? _self.endpointRef : endpointRef // ignore: cast_nullable_to_non_nullable
as String,discriminant: null == discriminant ? _self.discriminant : discriminant // ignore: cast_nullable_to_non_nullable
as String,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as RequestStatus,networkRequestId: freezed == networkRequestId ? _self.networkRequestId : networkRequestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallId: freezed == apiCallId ? _self.apiCallId : apiCallId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCapabilityEndpointId: freezed == apiCapabilityEndpointId ? _self.apiCapabilityEndpointId : apiCapabilityEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,callKey: freezed == callKey ? _self.callKey : callKey // ignore: cast_nullable_to_non_nullable
as UuidValue?,requestHash: freezed == requestHash ? _self.requestHash : requestHash // ignore: cast_nullable_to_non_nullable
as String?,requestModelId: freezed == requestModelId ? _self.requestModelId : requestModelId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeId: freezed == apiCallOutcomeId ? _self.apiCallOutcomeId : apiCallOutcomeId // ignore: cast_nullable_to_non_nullable
as UuidValue?,responseModelId: freezed == responseModelId ? _self.responseModelId : responseModelId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationId: freezed == serviceOperationId ? _self.serviceOperationId : serviceOperationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationConfigId: freezed == serviceOperationConfigId ? _self.serviceOperationConfigId : serviceOperationConfigId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationConfigApiEndpointId: freezed == serviceOperationConfigApiEndpointId ? _self.serviceOperationConfigApiEndpointId : serviceOperationConfigApiEndpointId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationCommitId: freezed == serviceOperationCommitId ? _self.serviceOperationCommitId : serviceOperationCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationHeadCommitId: freezed == serviceOperationHeadCommitId ? _self.serviceOperationHeadCommitId : serviceOperationHeadCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationBranchId: freezed == serviceOperationBranchId ? _self.serviceOperationBranchId : serviceOperationBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,serviceOperationProjectionHash: freezed == serviceOperationProjectionHash ? _self.serviceOperationProjectionHash : serviceOperationProjectionHash // ignore: cast_nullable_to_non_nullable
as String?,apiCallOutcomeCommitId: freezed == apiCallOutcomeCommitId ? _self.apiCallOutcomeCommitId : apiCallOutcomeCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeHeadCommitId: freezed == apiCallOutcomeHeadCommitId ? _self.apiCallOutcomeHeadCommitId : apiCallOutcomeHeadCommitId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeBranchId: freezed == apiCallOutcomeBranchId ? _self.apiCallOutcomeBranchId : apiCallOutcomeBranchId // ignore: cast_nullable_to_non_nullable
as UuidValue?,apiCallOutcomeProjectionHash: freezed == apiCallOutcomeProjectionHash ? _self.apiCallOutcomeProjectionHash : apiCallOutcomeProjectionHash // ignore: cast_nullable_to_non_nullable
as String?,economicReceipt: freezed == economicReceipt ? _self.economicReceipt : economicReceipt // ignore: cast_nullable_to_non_nullable
as ServiceOperationEconomicReceiptRefsV1?,
  ));
}

/// Create a copy of ServiceApiDispatchReceipt
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationEconomicReceiptRefsV1CopyWith<$Res>? get economicReceipt {
    if (_self.economicReceipt == null) {
    return null;
  }

  return $ServiceOperationEconomicReceiptRefsV1CopyWith<$Res>(_self.economicReceipt!, (value) {
    return _then(_self.copyWith(economicReceipt: value));
  });
}
}


/// @nodoc
mixin _$ServiceOperationRequest {

 ServiceOperationContext get context; String get service; Object? get operation; ServiceApiDispatchRequest? get apiDispatch;@UuidValueConverter() UuidValue? get streamTargetId;@UuidValueConverter() UuidValue? get streamCorrelationId;@UuidValueConverter() UuidValue? get networkRequestId;
/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceOperationRequestCopyWith<ServiceOperationRequest> get copyWith => _$ServiceOperationRequestCopyWithImpl<ServiceOperationRequest>(this as ServiceOperationRequest, _$identity);

  /// Serializes this ServiceOperationRequest to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceOperationRequest&&(identical(other.context, context) || other.context == context)&&(identical(other.service, service) || other.service == service)&&const DeepCollectionEquality().equals(other.operation, operation)&&(identical(other.apiDispatch, apiDispatch) || other.apiDispatch == apiDispatch)&&(identical(other.streamTargetId, streamTargetId) || other.streamTargetId == streamTargetId)&&(identical(other.streamCorrelationId, streamCorrelationId) || other.streamCorrelationId == streamCorrelationId)&&(identical(other.networkRequestId, networkRequestId) || other.networkRequestId == networkRequestId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,context,service,const DeepCollectionEquality().hash(operation),apiDispatch,streamTargetId,streamCorrelationId,networkRequestId);

@override
String toString() {
  return 'ServiceOperationRequest(context: $context, service: $service, operation: $operation, apiDispatch: $apiDispatch, streamTargetId: $streamTargetId, streamCorrelationId: $streamCorrelationId, networkRequestId: $networkRequestId)';
}


}

/// @nodoc
abstract mixin class $ServiceOperationRequestCopyWith<$Res>  {
  factory $ServiceOperationRequestCopyWith(ServiceOperationRequest value, $Res Function(ServiceOperationRequest) _then) = _$ServiceOperationRequestCopyWithImpl;
@useResult
$Res call({
 ServiceOperationContext context, String service, Object? operation, ServiceApiDispatchRequest? apiDispatch,@UuidValueConverter() UuidValue? streamTargetId,@UuidValueConverter() UuidValue? streamCorrelationId,@UuidValueConverter() UuidValue? networkRequestId
});


$ServiceOperationContextCopyWith<$Res> get context;$ServiceApiDispatchRequestCopyWith<$Res>? get apiDispatch;

}
/// @nodoc
class _$ServiceOperationRequestCopyWithImpl<$Res>
    implements $ServiceOperationRequestCopyWith<$Res> {
  _$ServiceOperationRequestCopyWithImpl(this._self, this._then);

  final ServiceOperationRequest _self;
  final $Res Function(ServiceOperationRequest) _then;

/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? context = null,Object? service = null,Object? operation = freezed,Object? apiDispatch = freezed,Object? streamTargetId = freezed,Object? streamCorrelationId = freezed,Object? networkRequestId = freezed,}) {
  return _then(_self.copyWith(
context: null == context ? _self.context : context // ignore: cast_nullable_to_non_nullable
as ServiceOperationContext,service: null == service ? _self.service : service // ignore: cast_nullable_to_non_nullable
as String,operation: freezed == operation ? _self.operation : operation ,apiDispatch: freezed == apiDispatch ? _self.apiDispatch : apiDispatch // ignore: cast_nullable_to_non_nullable
as ServiceApiDispatchRequest?,streamTargetId: freezed == streamTargetId ? _self.streamTargetId : streamTargetId // ignore: cast_nullable_to_non_nullable
as UuidValue?,streamCorrelationId: freezed == streamCorrelationId ? _self.streamCorrelationId : streamCorrelationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,networkRequestId: freezed == networkRequestId ? _self.networkRequestId : networkRequestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}
/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationContextCopyWith<$Res> get context {
  
  return $ServiceOperationContextCopyWith<$Res>(_self.context, (value) {
    return _then(_self.copyWith(context: value));
  });
}/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceApiDispatchRequestCopyWith<$Res>? get apiDispatch {
    if (_self.apiDispatch == null) {
    return null;
  }

  return $ServiceApiDispatchRequestCopyWith<$Res>(_self.apiDispatch!, (value) {
    return _then(_self.copyWith(apiDispatch: value));
  });
}
}


/// Adds pattern-matching-related methods to [ServiceOperationRequest].
extension ServiceOperationRequestPatterns on ServiceOperationRequest {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceOperationRequest value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceOperationRequest() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceOperationRequest value)  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationRequest():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceOperationRequest value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationRequest() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function( ServiceOperationContext context,  String service,  Object? operation,  ServiceApiDispatchRequest? apiDispatch, @UuidValueConverter()  UuidValue? streamTargetId, @UuidValueConverter()  UuidValue? streamCorrelationId, @UuidValueConverter()  UuidValue? networkRequestId)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceOperationRequest() when def != null:
return def(_that.context,_that.service,_that.operation,_that.apiDispatch,_that.streamTargetId,_that.streamCorrelationId,_that.networkRequestId);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function( ServiceOperationContext context,  String service,  Object? operation,  ServiceApiDispatchRequest? apiDispatch, @UuidValueConverter()  UuidValue? streamTargetId, @UuidValueConverter()  UuidValue? streamCorrelationId, @UuidValueConverter()  UuidValue? networkRequestId)  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationRequest():
return def(_that.context,_that.service,_that.operation,_that.apiDispatch,_that.streamTargetId,_that.streamCorrelationId,_that.networkRequestId);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function( ServiceOperationContext context,  String service,  Object? operation,  ServiceApiDispatchRequest? apiDispatch, @UuidValueConverter()  UuidValue? streamTargetId, @UuidValueConverter()  UuidValue? streamCorrelationId, @UuidValueConverter()  UuidValue? networkRequestId)?  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationRequest() when def != null:
return def(_that.context,_that.service,_that.operation,_that.apiDispatch,_that.streamTargetId,_that.streamCorrelationId,_that.networkRequestId);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceOperationRequest implements ServiceOperationRequest {
   _ServiceOperationRequest({required this.context, required this.service, this.operation, this.apiDispatch, @UuidValueConverter() this.streamTargetId, @UuidValueConverter() this.streamCorrelationId, @UuidValueConverter() this.networkRequestId});
  factory _ServiceOperationRequest.fromJson(Map<String, dynamic> json) => _$ServiceOperationRequestFromJson(json);

@override final  ServiceOperationContext context;
@override final  String service;
@override final  Object? operation;
@override final  ServiceApiDispatchRequest? apiDispatch;
@override@UuidValueConverter() final  UuidValue? streamTargetId;
@override@UuidValueConverter() final  UuidValue? streamCorrelationId;
@override@UuidValueConverter() final  UuidValue? networkRequestId;

/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceOperationRequestCopyWith<_ServiceOperationRequest> get copyWith => __$ServiceOperationRequestCopyWithImpl<_ServiceOperationRequest>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceOperationRequestToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceOperationRequest&&(identical(other.context, context) || other.context == context)&&(identical(other.service, service) || other.service == service)&&const DeepCollectionEquality().equals(other.operation, operation)&&(identical(other.apiDispatch, apiDispatch) || other.apiDispatch == apiDispatch)&&(identical(other.streamTargetId, streamTargetId) || other.streamTargetId == streamTargetId)&&(identical(other.streamCorrelationId, streamCorrelationId) || other.streamCorrelationId == streamCorrelationId)&&(identical(other.networkRequestId, networkRequestId) || other.networkRequestId == networkRequestId));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,context,service,const DeepCollectionEquality().hash(operation),apiDispatch,streamTargetId,streamCorrelationId,networkRequestId);

@override
String toString() {
  return 'ServiceOperationRequest.def(context: $context, service: $service, operation: $operation, apiDispatch: $apiDispatch, streamTargetId: $streamTargetId, streamCorrelationId: $streamCorrelationId, networkRequestId: $networkRequestId)';
}


}

/// @nodoc
abstract mixin class _$ServiceOperationRequestCopyWith<$Res> implements $ServiceOperationRequestCopyWith<$Res> {
  factory _$ServiceOperationRequestCopyWith(_ServiceOperationRequest value, $Res Function(_ServiceOperationRequest) _then) = __$ServiceOperationRequestCopyWithImpl;
@override @useResult
$Res call({
 ServiceOperationContext context, String service, Object? operation, ServiceApiDispatchRequest? apiDispatch,@UuidValueConverter() UuidValue? streamTargetId,@UuidValueConverter() UuidValue? streamCorrelationId,@UuidValueConverter() UuidValue? networkRequestId
});


@override $ServiceOperationContextCopyWith<$Res> get context;@override $ServiceApiDispatchRequestCopyWith<$Res>? get apiDispatch;

}
/// @nodoc
class __$ServiceOperationRequestCopyWithImpl<$Res>
    implements _$ServiceOperationRequestCopyWith<$Res> {
  __$ServiceOperationRequestCopyWithImpl(this._self, this._then);

  final _ServiceOperationRequest _self;
  final $Res Function(_ServiceOperationRequest) _then;

/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? context = null,Object? service = null,Object? operation = freezed,Object? apiDispatch = freezed,Object? streamTargetId = freezed,Object? streamCorrelationId = freezed,Object? networkRequestId = freezed,}) {
  return _then(_ServiceOperationRequest(
context: null == context ? _self.context : context // ignore: cast_nullable_to_non_nullable
as ServiceOperationContext,service: null == service ? _self.service : service // ignore: cast_nullable_to_non_nullable
as String,operation: freezed == operation ? _self.operation : operation ,apiDispatch: freezed == apiDispatch ? _self.apiDispatch : apiDispatch // ignore: cast_nullable_to_non_nullable
as ServiceApiDispatchRequest?,streamTargetId: freezed == streamTargetId ? _self.streamTargetId : streamTargetId // ignore: cast_nullable_to_non_nullable
as UuidValue?,streamCorrelationId: freezed == streamCorrelationId ? _self.streamCorrelationId : streamCorrelationId // ignore: cast_nullable_to_non_nullable
as UuidValue?,networkRequestId: freezed == networkRequestId ? _self.networkRequestId : networkRequestId // ignore: cast_nullable_to_non_nullable
as UuidValue?,
  ));
}

/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceOperationContextCopyWith<$Res> get context {
  
  return $ServiceOperationContextCopyWith<$Res>(_self.context, (value) {
    return _then(_self.copyWith(context: value));
  });
}/// Create a copy of ServiceOperationRequest
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceApiDispatchRequestCopyWith<$Res>? get apiDispatch {
    if (_self.apiDispatch == null) {
    return null;
  }

  return $ServiceApiDispatchRequestCopyWith<$Res>(_self.apiDispatch!, (value) {
    return _then(_self.copyWith(apiDispatch: value));
  });
}
}


/// @nodoc
mixin _$ServiceOperationResponse {

@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) RequestStatus get status; String? get error; Object? get responsePayload; ServiceApiDispatchReceipt? get receipt;@JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson) StreamLifecycle get streamLifecycle;
/// Create a copy of ServiceOperationResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$ServiceOperationResponseCopyWith<ServiceOperationResponse> get copyWith => _$ServiceOperationResponseCopyWithImpl<ServiceOperationResponse>(this as ServiceOperationResponse, _$identity);

  /// Serializes this ServiceOperationResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is ServiceOperationResponse&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.responsePayload, responsePayload)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.streamLifecycle, streamLifecycle) || other.streamLifecycle == streamLifecycle));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,status,error,const DeepCollectionEquality().hash(responsePayload),receipt,streamLifecycle);

@override
String toString() {
  return 'ServiceOperationResponse(status: $status, error: $error, responsePayload: $responsePayload, receipt: $receipt, streamLifecycle: $streamLifecycle)';
}


}

/// @nodoc
abstract mixin class $ServiceOperationResponseCopyWith<$Res>  {
  factory $ServiceOperationResponseCopyWith(ServiceOperationResponse value, $Res Function(ServiceOperationResponse) _then) = _$ServiceOperationResponseCopyWithImpl;
@useResult
$Res call({
@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) RequestStatus status, String? error, Object? responsePayload, ServiceApiDispatchReceipt? receipt,@JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson) StreamLifecycle streamLifecycle
});


$ServiceApiDispatchReceiptCopyWith<$Res>? get receipt;

}
/// @nodoc
class _$ServiceOperationResponseCopyWithImpl<$Res>
    implements $ServiceOperationResponseCopyWith<$Res> {
  _$ServiceOperationResponseCopyWithImpl(this._self, this._then);

  final ServiceOperationResponse _self;
  final $Res Function(ServiceOperationResponse) _then;

/// Create a copy of ServiceOperationResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? status = null,Object? error = freezed,Object? responsePayload = freezed,Object? receipt = freezed,Object? streamLifecycle = null,}) {
  return _then(_self.copyWith(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as RequestStatus,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,responsePayload: freezed == responsePayload ? _self.responsePayload : responsePayload ,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as ServiceApiDispatchReceipt?,streamLifecycle: null == streamLifecycle ? _self.streamLifecycle : streamLifecycle // ignore: cast_nullable_to_non_nullable
as StreamLifecycle,
  ));
}
/// Create a copy of ServiceOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceApiDispatchReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $ServiceApiDispatchReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}
}


/// Adds pattern-matching-related methods to [ServiceOperationResponse].
extension ServiceOperationResponsePatterns on ServiceOperationResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>({TResult Function( _ServiceOperationResponse value)?  def,required TResult orElse(),}){
final _that = this;
switch (_that) {
case _ServiceOperationResponse() when def != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>({required TResult Function( _ServiceOperationResponse value)  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>({TResult? Function( _ServiceOperationResponse value)?  def,}){
final _that = this;
switch (_that) {
case _ServiceOperationResponse() when def != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>({TResult Function(@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson)  RequestStatus status,  String? error,  Object? responsePayload,  ServiceApiDispatchReceipt? receipt, @JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson)  StreamLifecycle streamLifecycle)?  def,required TResult orElse(),}) {final _that = this;
switch (_that) {
case _ServiceOperationResponse() when def != null:
return def(_that.status,_that.error,_that.responsePayload,_that.receipt,_that.streamLifecycle);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>({required TResult Function(@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson)  RequestStatus status,  String? error,  Object? responsePayload,  ServiceApiDispatchReceipt? receipt, @JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson)  StreamLifecycle streamLifecycle)  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationResponse():
return def(_that.status,_that.error,_that.responsePayload,_that.receipt,_that.streamLifecycle);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>({TResult? Function(@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson)  RequestStatus status,  String? error,  Object? responsePayload,  ServiceApiDispatchReceipt? receipt, @JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson)  StreamLifecycle streamLifecycle)?  def,}) {final _that = this;
switch (_that) {
case _ServiceOperationResponse() when def != null:
return def(_that.status,_that.error,_that.responsePayload,_that.receipt,_that.streamLifecycle);case _:
  return null;

}
}

}

/// @nodoc

@JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
class _ServiceOperationResponse implements ServiceOperationResponse {
   _ServiceOperationResponse({@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) required this.status, this.error, this.responsePayload, this.receipt, @JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson) required this.streamLifecycle});
  factory _ServiceOperationResponse.fromJson(Map<String, dynamic> json) => _$ServiceOperationResponseFromJson(json);

@override@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) final  RequestStatus status;
@override final  String? error;
@override final  Object? responsePayload;
@override final  ServiceApiDispatchReceipt? receipt;
@override@JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson) final  StreamLifecycle streamLifecycle;

/// Create a copy of ServiceOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$ServiceOperationResponseCopyWith<_ServiceOperationResponse> get copyWith => __$ServiceOperationResponseCopyWithImpl<_ServiceOperationResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$ServiceOperationResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _ServiceOperationResponse&&(identical(other.status, status) || other.status == status)&&(identical(other.error, error) || other.error == error)&&const DeepCollectionEquality().equals(other.responsePayload, responsePayload)&&(identical(other.receipt, receipt) || other.receipt == receipt)&&(identical(other.streamLifecycle, streamLifecycle) || other.streamLifecycle == streamLifecycle));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,status,error,const DeepCollectionEquality().hash(responsePayload),receipt,streamLifecycle);

@override
String toString() {
  return 'ServiceOperationResponse.def(status: $status, error: $error, responsePayload: $responsePayload, receipt: $receipt, streamLifecycle: $streamLifecycle)';
}


}

/// @nodoc
abstract mixin class _$ServiceOperationResponseCopyWith<$Res> implements $ServiceOperationResponseCopyWith<$Res> {
  factory _$ServiceOperationResponseCopyWith(_ServiceOperationResponse value, $Res Function(_ServiceOperationResponse) _then) = __$ServiceOperationResponseCopyWithImpl;
@override @useResult
$Res call({
@JsonKey(fromJson: RequestStatusExtension.fromJson, toJson: RequestStatusExtension.toJson) RequestStatus status, String? error, Object? responsePayload, ServiceApiDispatchReceipt? receipt,@JsonKey(fromJson: StreamLifecycleExtension.fromJson, toJson: StreamLifecycleExtension.toJson) StreamLifecycle streamLifecycle
});


@override $ServiceApiDispatchReceiptCopyWith<$Res>? get receipt;

}
/// @nodoc
class __$ServiceOperationResponseCopyWithImpl<$Res>
    implements _$ServiceOperationResponseCopyWith<$Res> {
  __$ServiceOperationResponseCopyWithImpl(this._self, this._then);

  final _ServiceOperationResponse _self;
  final $Res Function(_ServiceOperationResponse) _then;

/// Create a copy of ServiceOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? status = null,Object? error = freezed,Object? responsePayload = freezed,Object? receipt = freezed,Object? streamLifecycle = null,}) {
  return _then(_ServiceOperationResponse(
status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as RequestStatus,error: freezed == error ? _self.error : error // ignore: cast_nullable_to_non_nullable
as String?,responsePayload: freezed == responsePayload ? _self.responsePayload : responsePayload ,receipt: freezed == receipt ? _self.receipt : receipt // ignore: cast_nullable_to_non_nullable
as ServiceApiDispatchReceipt?,streamLifecycle: null == streamLifecycle ? _self.streamLifecycle : streamLifecycle // ignore: cast_nullable_to_non_nullable
as StreamLifecycle,
  ));
}

/// Create a copy of ServiceOperationResponse
/// with the given fields replaced by the non-null parameter values.
@override
@pragma('vm:prefer-inline')
$ServiceApiDispatchReceiptCopyWith<$Res>? get receipt {
    if (_self.receipt == null) {
    return null;
  }

  return $ServiceApiDispatchReceiptCopyWith<$Res>(_self.receipt!, (value) {
    return _then(_self.copyWith(receipt: value));
  });
}
}

// dart format on
