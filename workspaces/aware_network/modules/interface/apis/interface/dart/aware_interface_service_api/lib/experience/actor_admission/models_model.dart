// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'models_model.freezed.dart';
part 'models_model.g.dart';

/// Canonical DTOs for Experience ActorConfig admission.
/// Ownership:
/// - Experience owns ActorConfig admission and role eligibility provenance.
/// - Identity owns concrete RoleAssignmentBinding truth.
/// - This DTO returns an Experience admission binding that carries Identity
/// binding ids without making Experience DTOs depend on Identity DTOs.
@freezed
abstract class ExperienceActorConfigRoleEligibility
    with _$ExperienceActorConfigRoleEligibility {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ExperienceActorConfigRoleEligibility.def({
    @UuidValueConverter() required UuidValue actorConfigRoleConfigId,
    @UuidValueConverter() required UuidValue roleConfigId,
    String? roleConfigName,
  }) = _ExperienceActorConfigRoleEligibility;

  factory ExperienceActorConfigRoleEligibility({
    required UuidValue actorConfigRoleConfigId,
    required UuidValue roleConfigId,
    String? roleConfigName,
  }) {
    return _ExperienceActorConfigRoleEligibility(
      actorConfigRoleConfigId: actorConfigRoleConfigId,
      roleConfigId: roleConfigId,
      roleConfigName: roleConfigName,
    );
  }

  factory ExperienceActorConfigRoleEligibility.fromJson(
    Map<String, dynamic> json,
  ) => _$ExperienceActorConfigRoleEligibilityFromJson(json);
}

@freezed
abstract class ExperienceActorConfigRoleAdmissionBinding
    with _$ExperienceActorConfigRoleAdmissionBinding {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ExperienceActorConfigRoleAdmissionBinding.def({
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
  }) = _ExperienceActorConfigRoleAdmissionBinding;

  factory ExperienceActorConfigRoleAdmissionBinding({
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
    return _ExperienceActorConfigRoleAdmissionBinding(
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

  factory ExperienceActorConfigRoleAdmissionBinding.fromJson(
    Map<String, dynamic> json,
  ) => _$ExperienceActorConfigRoleAdmissionBindingFromJson({
    ...json,
    if (!json.containsKey('object_instance_graph_branch_key'))
      'object_instance_graph_branch_key': 'all',
  });
}

@freezed
abstract class ExperienceActorConfigAdmissionReceipt
    with _$ExperienceActorConfigAdmissionReceipt {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ExperienceActorConfigAdmissionReceipt.def({
    required bool accepted,
    required String status,
    String? reason,
    required String experienceName,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? actorConfigId,
    @UuidValueConverter() UuidValue? classInstanceIdentityId,
    required String objectInstanceGraphBranchKey,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueListConverter()
    @Default(const [])
    List<UuidValue> requestedRoleConfigIds,
    @Default(const []) List<String> requestedRoleConfigNames,
    @Default(const []) List<ExperienceActorConfigRoleEligibility> eligibleRoles,
    @Default(const []) List<ExperienceActorConfigRoleAdmissionBinding> bindings,
    @Default(const []) List<String> blockers,
    required Map<String, dynamic> evidence,
  }) = _ExperienceActorConfigAdmissionReceipt;

  factory ExperienceActorConfigAdmissionReceipt({
    bool? accepted,
    required String status,
    String? reason,
    required String experienceName,
    UuidValue? actorId,
    UuidValue? actorConfigId,
    UuidValue? classInstanceIdentityId,
    String? objectInstanceGraphBranchKey,
    UuidValue? objectInstanceGraphBranchId,
    List<UuidValue> requestedRoleConfigIds = const [],
    List<String> requestedRoleConfigNames = const [],
    List<ExperienceActorConfigRoleEligibility> eligibleRoles = const [],
    List<ExperienceActorConfigRoleAdmissionBinding> bindings = const [],
    List<String> blockers = const [],
    Map<String, dynamic>? evidence,
  }) {
    return _ExperienceActorConfigAdmissionReceipt(
      accepted: accepted ?? false,
      status: status,
      reason: reason,
      experienceName: experienceName,
      actorId: actorId,
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

  factory ExperienceActorConfigAdmissionReceipt.fromJson(
    Map<String, dynamic> json,
  ) => _$ExperienceActorConfigAdmissionReceiptFromJson({
    ...json,
    if (!json.containsKey('accepted')) 'accepted': false,
    if (!json.containsKey('object_instance_graph_branch_key'))
      'object_instance_graph_branch_key': 'all',
    if (!json.containsKey('evidence')) 'evidence': {},
  });
}
