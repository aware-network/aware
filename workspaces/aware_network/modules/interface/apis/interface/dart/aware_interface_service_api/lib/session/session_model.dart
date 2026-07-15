// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'session_model.freezed.dart';
part 'session_model.g.dart';

@freezed
abstract class SessionSummary with _$SessionSummary {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SessionSummary.def({
    @UuidValueConverter() required UuidValue sessionId,
    @UuidValueConverter() required UuidValue sessionConfigId,
    @UuidValueConverter() UuidValue? parentSessionId,
    required String key,
    String? title,
    String? description,
    String? purpose,
    required String status,
    @UuidValueConverter() UuidValue? createdByActorId,
    String? sourceKind,
    String? sourceRef,
    required Map<String, dynamic> metadataJson,
    @Default(const []) List<SessionProviderSessionSummary> providerSessions,
    required int memberCount,
  }) = _SessionSummary;

  factory SessionSummary({
    required UuidValue sessionId,
    required UuidValue sessionConfigId,
    UuidValue? parentSessionId,
    required String key,
    String? title,
    String? description,
    String? purpose,
    String? status,
    UuidValue? createdByActorId,
    String? sourceKind,
    String? sourceRef,
    Map<String, dynamic>? metadataJson,
    List<SessionProviderSessionSummary> providerSessions = const [],
    int? memberCount,
  }) {
    return _SessionSummary(
      sessionId: sessionId,
      sessionConfigId: sessionConfigId,
      parentSessionId: parentSessionId,
      key: key,
      title: title,
      description: description,
      purpose: purpose,
      status: status ?? 'active',
      createdByActorId: createdByActorId,
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      metadataJson: metadataJson ?? {},
      providerSessions: providerSessions,
      memberCount: memberCount ?? 0,
    );
  }

  factory SessionSummary.fromJson(Map<String, dynamic> json) =>
      _$SessionSummaryFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('metadata_json')) 'metadata_json': {},
        if (!json.containsKey('member_count')) 'member_count': 0,
      });
}

@freezed
abstract class SessionMemberSummary with _$SessionMemberSummary {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SessionMemberSummary.def({
    @UuidValueConverter() required UuidValue sessionMemberId,
    @UuidValueConverter() required UuidValue sessionId,
    @UuidValueConverter() required UuidValue actorId,
    @UuidValueConverter() required UuidValue sessionActorConfigId,
    required String status,
    int? joinedAtUnixMs,
    int? leftAtUnixMs,
    required Map<String, dynamic> metadataJson,
    @Default(const []) List<SessionMemberActorRoleSummary> actorRoles,
  }) = _SessionMemberSummary;

  factory SessionMemberSummary({
    required UuidValue sessionMemberId,
    required UuidValue sessionId,
    required UuidValue actorId,
    required UuidValue sessionActorConfigId,
    String? status,
    int? joinedAtUnixMs,
    int? leftAtUnixMs,
    Map<String, dynamic>? metadataJson,
    List<SessionMemberActorRoleSummary> actorRoles = const [],
  }) {
    return _SessionMemberSummary(
      sessionMemberId: sessionMemberId,
      sessionId: sessionId,
      actorId: actorId,
      sessionActorConfigId: sessionActorConfigId,
      status: status ?? 'active',
      joinedAtUnixMs: joinedAtUnixMs,
      leftAtUnixMs: leftAtUnixMs,
      metadataJson: metadataJson ?? {},
      actorRoles: actorRoles,
    );
  }

  factory SessionMemberSummary.fromJson(Map<String, dynamic> json) =>
      _$SessionMemberSummaryFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('metadata_json')) 'metadata_json': {},
      });
}

@freezed
abstract class SessionMemberActorRoleSummary
    with _$SessionMemberActorRoleSummary {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SessionMemberActorRoleSummary.def({
    @UuidValueConverter() required UuidValue sessionMemberActorRoleId,
    @UuidValueConverter() required UuidValue sessionMemberId,
    @UuidValueConverter() required UuidValue actorRoleId,
    required String sourceKind,
    required String status,
    required Map<String, dynamic> evidenceJson,
  }) = _SessionMemberActorRoleSummary;

  factory SessionMemberActorRoleSummary({
    required UuidValue sessionMemberActorRoleId,
    required UuidValue sessionMemberId,
    required UuidValue actorRoleId,
    String? sourceKind,
    String? status,
    Map<String, dynamic>? evidenceJson,
  }) {
    return _SessionMemberActorRoleSummary(
      sessionMemberActorRoleId: sessionMemberActorRoleId,
      sessionMemberId: sessionMemberId,
      actorRoleId: actorRoleId,
      sourceKind: sourceKind ?? 'identity_session',
      status: status ?? 'active',
      evidenceJson: evidenceJson ?? {},
    );
  }

  factory SessionMemberActorRoleSummary.fromJson(Map<String, dynamic> json) =>
      _$SessionMemberActorRoleSummaryFromJson({
        ...json,
        if (!json.containsKey('source_kind')) 'source_kind': 'identity_session',
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('evidence_json')) 'evidence_json': {},
      });
}

@freezed
abstract class SessionProviderSessionSummary
    with _$SessionProviderSessionSummary {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory SessionProviderSessionSummary.def({
    @UuidValueConverter() required UuidValue sessionProviderSessionId,
    @UuidValueConverter() required UuidValue sessionId,
    @UuidValueConverter() required UuidValue providerSessionConfigId,
    required String providerSessionKey,
    String? providerSessionRef,
    @UuidValueConverter() UuidValue? providerObjectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? providerClassInstanceIdentityId,
    @UuidValueConverter() UuidValue? providerObjectInstanceGraphBranchId,
    required String status,
    required Map<String, dynamic> metadataJson,
  }) = _SessionProviderSessionSummary;

  factory SessionProviderSessionSummary({
    required UuidValue sessionProviderSessionId,
    required UuidValue sessionId,
    required UuidValue providerSessionConfigId,
    required String providerSessionKey,
    String? providerSessionRef,
    UuidValue? providerObjectInstanceGraphIdentityId,
    UuidValue? providerClassInstanceIdentityId,
    UuidValue? providerObjectInstanceGraphBranchId,
    String? status,
    Map<String, dynamic>? metadataJson,
  }) {
    return _SessionProviderSessionSummary(
      sessionProviderSessionId: sessionProviderSessionId,
      sessionId: sessionId,
      providerSessionConfigId: providerSessionConfigId,
      providerSessionKey: providerSessionKey,
      providerSessionRef: providerSessionRef,
      providerObjectInstanceGraphIdentityId:
          providerObjectInstanceGraphIdentityId,
      providerClassInstanceIdentityId: providerClassInstanceIdentityId,
      providerObjectInstanceGraphBranchId: providerObjectInstanceGraphBranchId,
      status: status ?? 'active',
      metadataJson: metadataJson ?? {},
    );
  }

  factory SessionProviderSessionSummary.fromJson(Map<String, dynamic> json) =>
      _$SessionProviderSessionSummaryFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('metadata_json')) 'metadata_json': {},
      });
}
