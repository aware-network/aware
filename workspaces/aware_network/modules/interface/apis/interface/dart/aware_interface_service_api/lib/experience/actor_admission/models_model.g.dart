// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'models_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_ExperienceActorConfigRoleEligibility
_$ExperienceActorConfigRoleEligibilityFromJson(Map<String, dynamic> json) =>
    _ExperienceActorConfigRoleEligibility(
      actorConfigRoleConfigId: const UuidValueConverter().fromJson(
        json['actor_config_role_config_id'] as String,
      ),
      roleConfigId: const UuidValueConverter().fromJson(
        json['role_config_id'] as String,
      ),
      roleConfigName: json['role_config_name'] as String?,
    );

Map<String, dynamic> _$ExperienceActorConfigRoleEligibilityToJson(
  _ExperienceActorConfigRoleEligibility instance,
) => <String, dynamic>{
  'actor_config_role_config_id': const UuidValueConverter().toJson(
    instance.actorConfigRoleConfigId,
  ),
  'role_config_id': const UuidValueConverter().toJson(instance.roleConfigId),
  'role_config_name': instance.roleConfigName,
};

_ExperienceActorConfigRoleAdmissionBinding
_$ExperienceActorConfigRoleAdmissionBindingFromJson(
  Map<String, dynamic> json,
) => _ExperienceActorConfigRoleAdmissionBinding(
  actorConfigRoleConfigId: const UuidValueConverter().fromJson(
    json['actor_config_role_config_id'] as String,
  ),
  roleConfigId: const UuidValueConverter().fromJson(
    json['role_config_id'] as String,
  ),
  roleConfigName: json['role_config_name'] as String?,
  actorId: const UuidValueConverter().fromJson(json['actor_id'] as String),
  roleId: const UuidValueConverter().fromJson(json['role_id'] as String),
  actorRoleId: const UuidValueConverter().fromJson(
    json['actor_role_id'] as String,
  ),
  roleClassInstanceId: const UuidValueConverter().fromJson(
    json['role_class_instance_id'] as String,
  ),
  classInstanceIdentityId: const UuidValueConverter().fromJson(
    json['class_instance_identity_id'] as String,
  ),
  roleConfigClassConfigId: const UuidValueConverter().fromJson(
    json['role_config_class_config_id'] as String,
  ),
  objectInstanceGraphIdentityId: const UuidValueConverter().fromJson(
    json['object_instance_graph_identity_id'] as String,
  ),
  objectInstanceGraphBranchKey:
      json['object_instance_graph_branch_key'] as String,
  objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_branch_id'],
    const UuidValueConverter().fromJson,
  ),
);

Map<String, dynamic> _$ExperienceActorConfigRoleAdmissionBindingToJson(
  _ExperienceActorConfigRoleAdmissionBinding instance,
) => <String, dynamic>{
  'actor_config_role_config_id': const UuidValueConverter().toJson(
    instance.actorConfigRoleConfigId,
  ),
  'role_config_id': const UuidValueConverter().toJson(instance.roleConfigId),
  'role_config_name': instance.roleConfigName,
  'actor_id': const UuidValueConverter().toJson(instance.actorId),
  'role_id': const UuidValueConverter().toJson(instance.roleId),
  'actor_role_id': const UuidValueConverter().toJson(instance.actorRoleId),
  'role_class_instance_id': const UuidValueConverter().toJson(
    instance.roleClassInstanceId,
  ),
  'class_instance_identity_id': const UuidValueConverter().toJson(
    instance.classInstanceIdentityId,
  ),
  'role_config_class_config_id': const UuidValueConverter().toJson(
    instance.roleConfigClassConfigId,
  ),
  'object_instance_graph_identity_id': const UuidValueConverter().toJson(
    instance.objectInstanceGraphIdentityId,
  ),
  'object_instance_graph_branch_key': instance.objectInstanceGraphBranchKey,
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_ExperienceActorConfigAdmissionReceipt
_$ExperienceActorConfigAdmissionReceiptFromJson(
  Map<String, dynamic> json,
) => _ExperienceActorConfigAdmissionReceipt(
  accepted: json['accepted'] as bool,
  status: json['status'] as String,
  reason: json['reason'] as String?,
  experienceName: json['experience_name'] as String,
  actorId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_id'],
    const UuidValueConverter().fromJson,
  ),
  actorConfigId: _$JsonConverterFromJson<String, UuidValue>(
    json['actor_config_id'],
    const UuidValueConverter().fromJson,
  ),
  classInstanceIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['class_instance_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  objectInstanceGraphBranchKey:
      json['object_instance_graph_branch_key'] as String,
  objectInstanceGraphBranchId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_instance_graph_branch_id'],
    const UuidValueConverter().fromJson,
  ),
  requestedRoleConfigIds: json['requested_role_config_ids'] == null
      ? const []
      : const UuidValueListConverter().fromJson(
          json['requested_role_config_ids'] as List,
        ),
  requestedRoleConfigNames:
      (json['requested_role_config_names'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      const [],
  eligibleRoles:
      (json['eligible_roles'] as List<dynamic>?)
          ?.map(
            (e) => ExperienceActorConfigRoleEligibility.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  bindings:
      (json['bindings'] as List<dynamic>?)
          ?.map(
            (e) => ExperienceActorConfigRoleAdmissionBinding.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  blockers:
      (json['blockers'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      const [],
  evidence: json['evidence'] as Map<String, dynamic>,
);

Map<String, dynamic> _$ExperienceActorConfigAdmissionReceiptToJson(
  _ExperienceActorConfigAdmissionReceipt instance,
) => <String, dynamic>{
  'accepted': instance.accepted,
  'status': instance.status,
  'reason': instance.reason,
  'experience_name': instance.experienceName,
  'actor_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorId,
    const UuidValueConverter().toJson,
  ),
  'actor_config_id': _$JsonConverterToJson<String, UuidValue>(
    instance.actorConfigId,
    const UuidValueConverter().toJson,
  ),
  'class_instance_identity_id': _$JsonConverterToJson<String, UuidValue>(
    instance.classInstanceIdentityId,
    const UuidValueConverter().toJson,
  ),
  'object_instance_graph_branch_key': instance.objectInstanceGraphBranchKey,
  'object_instance_graph_branch_id': _$JsonConverterToJson<String, UuidValue>(
    instance.objectInstanceGraphBranchId,
    const UuidValueConverter().toJson,
  ),
  'requested_role_config_ids': const UuidValueListConverter().toJson(
    instance.requestedRoleConfigIds,
  ),
  'requested_role_config_names': instance.requestedRoleConfigNames,
  'eligible_roles': instance.eligibleRoles.map((e) => e.toJson()).toList(),
  'bindings': instance.bindings.map((e) => e.toJson()).toList(),
  'blockers': instance.blockers,
  'evidence': instance.evidence,
};
