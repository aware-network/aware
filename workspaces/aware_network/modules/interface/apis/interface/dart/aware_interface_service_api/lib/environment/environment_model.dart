// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import '../session/session_model.dart';
import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'environment_model.freezed.dart';
part 'environment_model.g.dart';

@freezed
abstract class EnvironmentActorAdmissionRoleEligibility
    with _$EnvironmentActorAdmissionRoleEligibility {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentActorAdmissionRoleEligibility.def({
    @UuidValueConverter() required UuidValue environmentProfileActorConfigId,
    @UuidValueConverter() required UuidValue actorConfigRoleConfigId,
    @UuidValueConverter() required UuidValue roleConfigId,
    String? roleConfigName,
  }) = _EnvironmentActorAdmissionRoleEligibility;

  factory EnvironmentActorAdmissionRoleEligibility({
    required UuidValue environmentProfileActorConfigId,
    required UuidValue actorConfigRoleConfigId,
    required UuidValue roleConfigId,
    String? roleConfigName,
  }) {
    return _EnvironmentActorAdmissionRoleEligibility(
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigRoleConfigId: actorConfigRoleConfigId,
      roleConfigId: roleConfigId,
      roleConfigName: roleConfigName,
    );
  }

  factory EnvironmentActorAdmissionRoleEligibility.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentActorAdmissionRoleEligibilityFromJson(json);
}

@freezed
abstract class EnvironmentActorAdmissionRoleBinding
    with _$EnvironmentActorAdmissionRoleBinding {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentActorAdmissionRoleBinding.def({
    @UuidValueConverter() required UuidValue environmentProfileActorConfigId,
    @UuidValueConverter() required UuidValue actorConfigRoleConfigId,
    @UuidValueConverter() required UuidValue roleConfigId,
    String? roleConfigName,
    @UuidValueConverter() required UuidValue actorId,
    @UuidValueConverter() required UuidValue roleId,
    @UuidValueConverter() required UuidValue actorRoleId,
    @UuidValueConverter() required UuidValue roleClassInstanceId,
    @UuidValueConverter() required UuidValue classInstanceIdentityId,
    @UuidValueConverter() required UuidValue roleConfigClassConfigId,
    @UuidValueConverter() required UuidValue objectInstanceGraphIdentityId,
    required String objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
  }) = _EnvironmentActorAdmissionRoleBinding;

  factory EnvironmentActorAdmissionRoleBinding({
    required UuidValue environmentProfileActorConfigId,
    required UuidValue actorConfigRoleConfigId,
    required UuidValue roleConfigId,
    String? roleConfigName,
    required UuidValue actorId,
    required UuidValue roleId,
    required UuidValue actorRoleId,
    required UuidValue roleClassInstanceId,
    required UuidValue classInstanceIdentityId,
    required UuidValue roleConfigClassConfigId,
    required UuidValue objectInstanceGraphIdentityId,
    String? objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
  }) {
    return _EnvironmentActorAdmissionRoleBinding(
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigRoleConfigId: actorConfigRoleConfigId,
      roleConfigId: roleConfigId,
      roleConfigName: roleConfigName,
      actorId: actorId,
      roleId: roleId,
      actorRoleId: actorRoleId,
      roleClassInstanceId: roleClassInstanceId,
      classInstanceIdentityId: classInstanceIdentityId,
      roleConfigClassConfigId: roleConfigClassConfigId,
      objectInstanceGraphIdentityId: objectInstanceGraphIdentityId,
      objectInstanceGraphBranchKey: objectInstanceGraphBranchKey ?? 'all',
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
    );
  }

  factory EnvironmentActorAdmissionRoleBinding.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentActorAdmissionRoleBindingFromJson({
    ...json,
    if (!json.containsKey('object_instance_graph_branch_key'))
      'object_instance_graph_branch_key': 'all',
  });
}

@freezed
abstract class EnvironmentActorAdmissionReceipt
    with _$EnvironmentActorAdmissionReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentActorAdmissionReceipt.def({
    required bool accepted,
    required String status,
    String? error,
    String? reason,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    @UuidValueConverter() UuidValue? environmentProfileActorConfigId,
    @UuidValueConverter() UuidValue? actorConfigId,
    @UuidValueConverter() UuidValue? classInstanceIdentityId,
    required String objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> requestedRoleConfigIds,
    @Default(const []) List<String> requestedRoleConfigNames,
    @Default(const [])
    List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles,
    @Default(const []) List<EnvironmentActorAdmissionRoleBinding> bindings,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentActorAdmissionReceipt;

  factory EnvironmentActorAdmissionReceipt({
    bool? accepted,
    required String status,
    String? error,
    String? reason,
    UuidValue? actorId,
    required UuidValue environmentId,
    required UuidValue environmentProfileId,
    UuidValue? environmentProfileActorConfigId,
    UuidValue? actorConfigId,
    UuidValue? classInstanceIdentityId,
    String? objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
    List<UuidValue> requestedRoleConfigIds = const [],
    List<String> requestedRoleConfigNames = const [],
    List<EnvironmentActorAdmissionRoleEligibility> eligibleRoles = const [],
    List<EnvironmentActorAdmissionRoleBinding> bindings = const [],
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentActorAdmissionReceipt(
      accepted: accepted ?? false,
      status: status,
      error: error,
      reason: reason,
      actorId: actorId,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      environmentProfileActorConfigId: environmentProfileActorConfigId,
      actorConfigId: actorConfigId,
      classInstanceIdentityId: classInstanceIdentityId,
      objectInstanceGraphBranchKey: objectInstanceGraphBranchKey ?? 'all',
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      requestedRoleConfigIds: requestedRoleConfigIds,
      requestedRoleConfigNames: requestedRoleConfigNames,
      eligibleRoles: eligibleRoles,
      bindings: bindings,
      blockers: blockers,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentActorAdmissionReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentActorAdmissionReceiptFromJson({
    ...json,
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('object_instance_graph_branch_key'))
      'object_instance_graph_branch_key': 'all',
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class EnvironmentSessionIdentityEvidence
    with _$EnvironmentSessionIdentityEvidence {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentSessionIdentityEvidence.def({
    SessionSummary? identitySession,
    SessionMemberSummary? identityMember,
    @Default(const []) List<SessionMemberActorRoleSummary> identityActorRoles,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentSessionIdentityEvidence;

  factory EnvironmentSessionIdentityEvidence({
    SessionSummary? identitySession,
    SessionMemberSummary? identityMember,
    List<SessionMemberActorRoleSummary> identityActorRoles = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentSessionIdentityEvidence(
      identitySession: identitySession,
      identityMember: identityMember,
      identityActorRoles: identityActorRoles,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentSessionIdentityEvidence.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentSessionIdentityEvidenceFromJson({
    ...json,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class EnvironmentSessionView with _$EnvironmentSessionView {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentSessionView.def({
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() UuidValue? environmentSessionConfigId,
    @UuidValueConverter() UuidValue? identitySessionId,
    SessionSummary? identitySession,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    required String sessionKey,
    String? title,
    String? description,
    String? purpose,
    required String status,
    @UuidValueConverter() UuidValue? createdByActorId,
    String? sourceKind,
    String? sourceRef,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentSessionView;

  factory EnvironmentSessionView({
    required UuidValue environmentSessionId,
    UuidValue? environmentSessionConfigId,
    UuidValue? identitySessionId,
    SessionSummary? identitySession,
    required UuidValue environmentId,
    required UuidValue environmentProfileId,
    required String sessionKey,
    String? title,
    String? description,
    String? purpose,
    String? status,
    UuidValue? createdByActorId,
    String? sourceKind,
    String? sourceRef,
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentSessionView(
      environmentSessionId: environmentSessionId,
      environmentSessionConfigId: environmentSessionConfigId,
      identitySessionId: identitySessionId,
      identitySession: identitySession,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      sessionKey: sessionKey,
      title: title,
      description: description,
      purpose: purpose,
      status: status ?? 'active',
      createdByActorId: createdByActorId,
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentSessionView.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentSessionViewFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class EnvironmentSessionJoinReceipt
    with _$EnvironmentSessionJoinReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentSessionJoinReceipt.def({
    required bool accepted,
    required String status,
    String? error,
    String? reason,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentProfileId,
    @UuidValueConverter() UuidValue? environmentSessionId,
    String? environmentSessionKey,
    EnvironmentSessionIdentityEvidence? identityEvidence,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentSessionJoinReceipt;

  factory EnvironmentSessionJoinReceipt({
    bool? accepted,
    required String status,
    String? error,
    String? reason,
    UuidValue? actorId,
    required UuidValue environmentId,
    required UuidValue environmentProfileId,
    UuidValue? environmentSessionId,
    String? environmentSessionKey,
    EnvironmentSessionIdentityEvidence? identityEvidence,
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentSessionJoinReceipt(
      accepted: accepted ?? false,
      status: status,
      error: error,
      reason: reason,
      actorId: actorId,
      environmentId: environmentId,
      environmentProfileId: environmentProfileId,
      environmentSessionId: environmentSessionId,
      environmentSessionKey: environmentSessionKey,
      identityEvidence: identityEvidence,
      blockers: blockers,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentSessionJoinReceipt.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentSessionJoinReceiptFromJson({
        ...json,
        if (!json.containsKey('accepted')) 'accepted': false,
        if (!json.containsKey('evidence')) 'evidence': {},
      });
}

@freezed
abstract class EnvironmentNavigationContextView
    with _$EnvironmentNavigationContextView {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentNavigationContextView.def({
    @UuidValueConverter() required UuidValue environmentNavigationContextId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() required UuidValue environmentId,
    required String key,
    String? title,
    required String status,
    required bool isDefault,
    @UuidValueConverter() UuidValue? selectedProcessId,
    @UuidValueConverter() UuidValue? selectedThreadId,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? rootObjectId,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentNavigationContextView;

  factory EnvironmentNavigationContextView({
    required UuidValue environmentNavigationContextId,
    required UuidValue environmentSessionId,
    required UuidValue environmentId,
    required String key,
    String? title,
    String? status,
    bool? isDefault,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? rootObjectId,
    UuidValue? commitId,
    UuidValue? objectInstanceGraphCommitId,
    String? graphHashPost,
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentNavigationContextView(
      environmentNavigationContextId: environmentNavigationContextId,
      environmentSessionId: environmentSessionId,
      environmentId: environmentId,
      key: key,
      title: title,
      status: status ?? 'active',
      isDefault: isDefault ?? false,
      selectedProcessId: selectedProcessId,
      selectedThreadId: selectedThreadId,
      branchId: branchId,
      projectionHash: projectionHash,
      rootObjectId: rootObjectId,
      commitId: commitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      graphHashPost: graphHashPost,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentNavigationContextView.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentNavigationContextViewFromJson({
    ...json,
    if (!json.containsKey('status')) 'status': 'active',
    if (!json.containsKey('is_default')) 'is_default': false,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}

@freezed
abstract class EnvironmentNavigationCommitReceipt
    with _$EnvironmentNavigationCommitReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentNavigationCommitReceipt.def({
    required bool accepted,
    required String status,
    String? error,
    String? reason,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() required UuidValue environmentId,
    @UuidValueConverter() required UuidValue environmentSessionId,
    @UuidValueConverter() UuidValue? environmentNavigationContextId,
    String? key,
    required bool isDefault,
    @UuidValueConverter() UuidValue? branchId,
    String? projectionHash,
    @UuidValueConverter() UuidValue? rootObjectId,
    @UuidValueConverter() UuidValue? commitId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    String? graphHashPre,
    String? graphHashPost,
    @UuidValueConverter() UuidValue? functionCallId,
    @UuidValueConverter() UuidValue? functionCallResponseId,
    @UuidValueConverter() UuidValue? selectedProcessId,
    @UuidValueConverter() UuidValue? selectedThreadId,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _EnvironmentNavigationCommitReceipt;

  factory EnvironmentNavigationCommitReceipt({
    bool? accepted,
    required String status,
    String? error,
    String? reason,
    UuidValue? actorId,
    required UuidValue environmentId,
    required UuidValue environmentSessionId,
    UuidValue? environmentNavigationContextId,
    String? key,
    bool? isDefault,
    UuidValue? branchId,
    String? projectionHash,
    UuidValue? rootObjectId,
    UuidValue? commitId,
    UuidValue? objectInstanceGraphCommitId,
    String? graphHashPre,
    String? graphHashPost,
    UuidValue? functionCallId,
    UuidValue? functionCallResponseId,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _EnvironmentNavigationCommitReceipt(
      accepted: accepted ?? false,
      status: status,
      error: error,
      reason: reason,
      actorId: actorId,
      environmentId: environmentId,
      environmentSessionId: environmentSessionId,
      environmentNavigationContextId: environmentNavigationContextId,
      key: key,
      isDefault: isDefault ?? false,
      branchId: branchId,
      projectionHash: projectionHash,
      rootObjectId: rootObjectId,
      commitId: commitId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      graphHashPre: graphHashPre,
      graphHashPost: graphHashPost,
      functionCallId: functionCallId,
      functionCallResponseId: functionCallResponseId,
      selectedProcessId: selectedProcessId,
      selectedThreadId: selectedThreadId,
      blockers: blockers,
      evidence: evidence ?? {},
    );
  }

  factory EnvironmentNavigationCommitReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentNavigationCommitReceiptFromJson({
    ...json,
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('is_default')) 'is_default': false,
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}
