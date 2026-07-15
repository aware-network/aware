// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'interface_config_bundle_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_InterfaceConfigApiBundle _$InterfaceConfigApiBundleFromJson(
  Map<String, dynamic> json,
) => _InterfaceConfigApiBundle(
  interfaceConfigApiId: const UuidValueConverter().fromJson(
    json['interface_config_api_id'] as String,
  ),
  apiId: const UuidValueConverter().fromJson(json['api_id'] as String),
  apiRef: json['api_ref'] as String,
);

Map<String, dynamic> _$InterfaceConfigApiBundleToJson(
  _InterfaceConfigApiBundle instance,
) => <String, dynamic>{
  'interface_config_api_id': const UuidValueConverter().toJson(
    instance.interfaceConfigApiId,
  ),
  'api_id': const UuidValueConverter().toJson(instance.apiId),
  'api_ref': instance.apiRef,
};

_InterfaceWindowLayoutSectionBundle
_$InterfaceWindowLayoutSectionBundleFromJson(Map<String, dynamic> json) =>
    _InterfaceWindowLayoutSectionBundle(
      layoutConfigSectionConfigId: const UuidValueConverter().fromJson(
        json['layout_config_section_config_id'] as String,
      ),
      key: json['key'] as String,
    );

Map<String, dynamic> _$InterfaceWindowLayoutSectionBundleToJson(
  _InterfaceWindowLayoutSectionBundle instance,
) => <String, dynamic>{
  'layout_config_section_config_id': const UuidValueConverter().toJson(
    instance.layoutConfigSectionConfigId,
  ),
  'key': instance.key,
};

_InterfaceWindowConfigLayoutBundle _$InterfaceWindowConfigLayoutBundleFromJson(
  Map<String, dynamic> json,
) => _InterfaceWindowConfigLayoutBundle(
  windowConfigLayoutConfigId: const UuidValueConverter().fromJson(
    json['window_config_layout_config_id'] as String,
  ),
  layoutConfigId: const UuidValueConverter().fromJson(
    json['layout_config_id'] as String,
  ),
  key: json['key'] as String,
  isDefault: json['is_default'] as bool,
  sections:
      (json['sections'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceWindowLayoutSectionBundle.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceWindowConfigLayoutBundleToJson(
  _InterfaceWindowConfigLayoutBundle instance,
) => <String, dynamic>{
  'window_config_layout_config_id': const UuidValueConverter().toJson(
    instance.windowConfigLayoutConfigId,
  ),
  'layout_config_id': const UuidValueConverter().toJson(
    instance.layoutConfigId,
  ),
  'key': instance.key,
  'is_default': instance.isDefault,
  'sections': instance.sections.map((e) => e.toJson()).toList(),
};

_InterfaceWindowConfigBundle _$InterfaceWindowConfigBundleFromJson(
  Map<String, dynamic> json,
) => _InterfaceWindowConfigBundle(
  interfaceConfigWindowConfigId: const UuidValueConverter().fromJson(
    json['interface_config_window_config_id'] as String,
  ),
  windowConfigId: const UuidValueConverter().fromJson(
    json['window_config_id'] as String,
  ),
  key: json['key'] as String,
  description: json['description'] as String?,
  layoutConfigs:
      (json['layout_configs'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceWindowConfigLayoutBundle.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceWindowConfigBundleToJson(
  _InterfaceWindowConfigBundle instance,
) => <String, dynamic>{
  'interface_config_window_config_id': const UuidValueConverter().toJson(
    instance.interfaceConfigWindowConfigId,
  ),
  'window_config_id': const UuidValueConverter().toJson(
    instance.windowConfigId,
  ),
  'key': instance.key,
  'description': instance.description,
  'layout_configs': instance.layoutConfigs.map((e) => e.toJson()).toList(),
};

_InterfacePaneSectionMountBundle _$InterfacePaneSectionMountBundleFromJson(
  Map<String, dynamic> json,
) => _InterfacePaneSectionMountBundle(
  mountId: const UuidValueConverter().fromJson(json['mount_id'] as String),
  layoutConfigSectionConfigId: const UuidValueConverter().fromJson(
    json['layout_config_section_config_id'] as String,
  ),
);

Map<String, dynamic> _$InterfacePaneSectionMountBundleToJson(
  _InterfacePaneSectionMountBundle instance,
) => <String, dynamic>{
  'mount_id': const UuidValueConverter().toJson(instance.mountId),
  'layout_config_section_config_id': const UuidValueConverter().toJson(
    instance.layoutConfigSectionConfigId,
  ),
};

_InterfacePaneViewInvocationActionBundle
_$InterfacePaneViewInvocationActionBundleFromJson(Map<String, dynamic> json) =>
    _InterfacePaneViewInvocationActionBundle(
      projectionExperienceViewInvocationActionId: const UuidValueConverter()
          .fromJson(
            json['projection_experience_view_invocation_action_id'] as String,
          ),
      actionKey: json['action_key'] as String,
      actionKind: json['action_kind'] as String,
      targetRef: json['target_ref'] as String,
      apiCapabilityEndpointId: _$JsonConverterFromJson<String, UuidValue>(
        json['api_capability_endpoint_id'],
        const UuidValueConverter().fromJson,
      ),
      sdkOperationId: _$JsonConverterFromJson<String, UuidValue>(
        json['sdk_operation_id'],
        const UuidValueConverter().fromJson,
      ),
      label: json['label'] as String?,
      receiptPolicy: json['receipt_policy'] as String?,
      confirmationPolicy: json['confirmation_policy'] as String?,
      optimisticPolicy: json['optimistic_policy'] as String?,
    );

Map<String, dynamic> _$InterfacePaneViewInvocationActionBundleToJson(
  _InterfacePaneViewInvocationActionBundle instance,
) => <String, dynamic>{
  'projection_experience_view_invocation_action_id': const UuidValueConverter()
      .toJson(instance.projectionExperienceViewInvocationActionId),
  'action_key': instance.actionKey,
  'action_kind': instance.actionKind,
  'target_ref': instance.targetRef,
  'api_capability_endpoint_id': _$JsonConverterToJson<String, UuidValue>(
    instance.apiCapabilityEndpointId,
    const UuidValueConverter().toJson,
  ),
  'sdk_operation_id': _$JsonConverterToJson<String, UuidValue>(
    instance.sdkOperationId,
    const UuidValueConverter().toJson,
  ),
  'label': instance.label,
  'receipt_policy': instance.receiptPolicy,
  'confirmation_policy': instance.confirmationPolicy,
  'optimistic_policy': instance.optimisticPolicy,
};

Value? _$JsonConverterFromJson<Json, Value>(
  Object? json,
  Value? Function(Json json) fromJson,
) => json == null ? null : fromJson(json as Json);

Json? _$JsonConverterToJson<Json, Value>(
  Value? value,
  Json? Function(Value value) toJson,
) => value == null ? null : toJson(value);

_InterfacePaneProjectionExperienceViewBundle
_$InterfacePaneProjectionExperienceViewBundleFromJson(
  Map<String, dynamic> json,
) => _InterfacePaneProjectionExperienceViewBundle(
  bindingId: const UuidValueConverter().fromJson(json['binding_id'] as String),
  projectionExperienceViewId: const UuidValueConverter().fromJson(
    json['projection_experience_view_id'] as String,
  ),
  objectProjectionGraphObservableId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_observable_id'],
    const UuidValueConverter().fromJson,
  ),
  projectionExperienceGraphIdentityId:
      _$JsonConverterFromJson<String, UuidValue>(
        json['projection_experience_graph_identity_id'],
        const UuidValueConverter().fromJson,
      ),
  objectProjectionGraphIdentityId: _$JsonConverterFromJson<String, UuidValue>(
    json['object_projection_graph_identity_id'],
    const UuidValueConverter().fromJson,
  ),
  sectionGraphBindingKey: json['section_graph_binding_key'] as String?,
  stateModelId: _$JsonConverterFromJson<String, UuidValue>(
    json['state_model_id'],
    const UuidValueConverter().fromJson,
  ),
  viewRef: json['view_ref'] as String,
  projectionViewKey: json['projection_view_key'] as String?,
  isDefault: json['is_default'] as bool,
  invocationActions:
      (json['invocation_actions'] as List<dynamic>?)
          ?.map(
            (e) => InterfacePaneViewInvocationActionBundle.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  sectionMounts:
      (json['section_mounts'] as List<dynamic>?)
          ?.map(
            (e) => InterfacePaneSectionMountBundle.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfacePaneProjectionExperienceViewBundleToJson(
  _InterfacePaneProjectionExperienceViewBundle instance,
) => <String, dynamic>{
  'binding_id': const UuidValueConverter().toJson(instance.bindingId),
  'projection_experience_view_id': const UuidValueConverter().toJson(
    instance.projectionExperienceViewId,
  ),
  'object_projection_graph_observable_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphObservableId,
        const UuidValueConverter().toJson,
      ),
  'projection_experience_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.projectionExperienceGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'object_projection_graph_identity_id':
      _$JsonConverterToJson<String, UuidValue>(
        instance.objectProjectionGraphIdentityId,
        const UuidValueConverter().toJson,
      ),
  'section_graph_binding_key': instance.sectionGraphBindingKey,
  'state_model_id': _$JsonConverterToJson<String, UuidValue>(
    instance.stateModelId,
    const UuidValueConverter().toJson,
  ),
  'view_ref': instance.viewRef,
  'projection_view_key': instance.projectionViewKey,
  'is_default': instance.isDefault,
  'invocation_actions': instance.invocationActions
      .map((e) => e.toJson())
      .toList(),
  'section_mounts': instance.sectionMounts.map((e) => e.toJson()).toList(),
};

_InterfacePaneApiCapabilityEndpointBundle
_$InterfacePaneApiCapabilityEndpointBundleFromJson(Map<String, dynamic> json) =>
    _InterfacePaneApiCapabilityEndpointBundle(
      bindingId: const UuidValueConverter().fromJson(
        json['binding_id'] as String,
      ),
      apiCapabilityEndpointId: const UuidValueConverter().fromJson(
        json['api_capability_endpoint_id'] as String,
      ),
      endpointRef: json['endpoint_ref'] as String?,
      discriminant: json['discriminant'] as String?,
    );

Map<String, dynamic> _$InterfacePaneApiCapabilityEndpointBundleToJson(
  _InterfacePaneApiCapabilityEndpointBundle instance,
) => <String, dynamic>{
  'binding_id': const UuidValueConverter().toJson(instance.bindingId),
  'api_capability_endpoint_id': const UuidValueConverter().toJson(
    instance.apiCapabilityEndpointId,
  ),
  'endpoint_ref': instance.endpointRef,
  'discriminant': instance.discriminant,
};

_InterfacePaneSdkOperationBundle _$InterfacePaneSdkOperationBundleFromJson(
  Map<String, dynamic> json,
) => _InterfacePaneSdkOperationBundle(
  bindingId: const UuidValueConverter().fromJson(json['binding_id'] as String),
  sdkOperationId: const UuidValueConverter().fromJson(
    json['sdk_operation_id'] as String,
  ),
  operationRef: json['operation_ref'] as String?,
  discriminant: json['discriminant'] as String?,
);

Map<String, dynamic> _$InterfacePaneSdkOperationBundleToJson(
  _InterfacePaneSdkOperationBundle instance,
) => <String, dynamic>{
  'binding_id': const UuidValueConverter().toJson(instance.bindingId),
  'sdk_operation_id': const UuidValueConverter().toJson(
    instance.sdkOperationId,
  ),
  'operation_ref': instance.operationRef,
  'discriminant': instance.discriminant,
};

_InterfacePaneConfigBundle _$InterfacePaneConfigBundleFromJson(
  Map<String, dynamic> json,
) => _InterfacePaneConfigBundle(
  paneConfigId: const UuidValueConverter().fromJson(
    json['pane_config_id'] as String,
  ),
  panePackageId: _$JsonConverterFromJson<String, UuidValue>(
    json['pane_package_id'],
    const UuidValueConverter().fromJson,
  ),
  panePackageName: json['pane_package_name'] as String?,
  name: json['name'] as String,
  paneKind: json['pane_kind'] as String,
  description: json['description'] as String?,
  narrativeKey: json['narrative_key'] as String?,
  projectionExperienceViews:
      (json['projection_experience_views'] as List<dynamic>?)
          ?.map(
            (e) => InterfacePaneProjectionExperienceViewBundle.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  apiCapabilityEndpoints:
      (json['api_capability_endpoints'] as List<dynamic>?)
          ?.map(
            (e) => InterfacePaneApiCapabilityEndpointBundle.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
  sdkOperations:
      (json['sdk_operations'] as List<dynamic>?)
          ?.map(
            (e) => InterfacePaneSdkOperationBundle.fromJson(
              e as Map<String, dynamic>,
            ),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfacePaneConfigBundleToJson(
  _InterfacePaneConfigBundle instance,
) => <String, dynamic>{
  'pane_config_id': const UuidValueConverter().toJson(instance.paneConfigId),
  'pane_package_id': _$JsonConverterToJson<String, UuidValue>(
    instance.panePackageId,
    const UuidValueConverter().toJson,
  ),
  'pane_package_name': instance.panePackageName,
  'name': instance.name,
  'pane_kind': instance.paneKind,
  'description': instance.description,
  'narrative_key': instance.narrativeKey,
  'projection_experience_views': instance.projectionExperienceViews
      .map((e) => e.toJson())
      .toList(),
  'api_capability_endpoints': instance.apiCapabilityEndpoints
      .map((e) => e.toJson())
      .toList(),
  'sdk_operations': instance.sdkOperations.map((e) => e.toJson()).toList(),
};

_InterfaceConfigBundle _$InterfaceConfigBundleFromJson(
  Map<String, dynamic> json,
) => _InterfaceConfigBundle(
  interfacePackageId: const UuidValueConverter().fromJson(
    json['interface_package_id'] as String,
  ),
  interfacePackageName: json['interface_package_name'] as String,
  interfaceConfigId: const UuidValueConverter().fromJson(
    json['interface_config_id'] as String,
  ),
  name: json['name'] as String,
  description: json['description'] as String?,
  apis:
      (json['apis'] as List<dynamic>?)
          ?.map(
            (e) => InterfaceConfigApiBundle.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  windowConfigs:
      (json['window_configs'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfaceWindowConfigBundle.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
  paneConfigs:
      (json['pane_configs'] as List<dynamic>?)
          ?.map(
            (e) =>
                InterfacePaneConfigBundle.fromJson(e as Map<String, dynamic>),
          )
          .toList() ??
      const [],
);

Map<String, dynamic> _$InterfaceConfigBundleToJson(
  _InterfaceConfigBundle instance,
) => <String, dynamic>{
  'interface_package_id': const UuidValueConverter().toJson(
    instance.interfacePackageId,
  ),
  'interface_package_name': instance.interfacePackageName,
  'interface_config_id': const UuidValueConverter().toJson(
    instance.interfaceConfigId,
  ),
  'name': instance.name,
  'description': instance.description,
  'apis': instance.apis.map((e) => e.toJson()).toList(),
  'window_configs': instance.windowConfigs.map((e) => e.toJson()).toList(),
  'pane_configs': instance.paneConfigs.map((e) => e.toJson()).toList(),
};
