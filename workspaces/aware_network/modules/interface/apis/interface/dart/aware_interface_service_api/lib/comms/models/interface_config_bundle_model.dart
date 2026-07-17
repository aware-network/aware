// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'interface_config_bundle_model.freezed.dart';
part 'interface_config_bundle_model.g.dart';

/// Canonical bundle-facing Interface config DTOs.
/// These types are transport-neutral read/write contracts for authored or
/// compiled Interface configuration payloads before they are materialized into
/// canonical Interface ontology truth. They are intentionally scoped to
/// configuration semantics, not live renderer state.
@freezed
abstract class InterfaceConfigApiBundle with _$InterfaceConfigApiBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceConfigApiBundle.def({
    @UuidValueConverter() required UuidValue interfaceConfigApiId,
    @UuidValueConverter() required UuidValue apiId,
    required String apiRef,
  }) = _InterfaceConfigApiBundle;

  factory InterfaceConfigApiBundle({
    required UuidValue interfaceConfigApiId,
    required UuidValue apiId,
    required String apiRef,
  }) {
    return _InterfaceConfigApiBundle(
      interfaceConfigApiId: interfaceConfigApiId,
      apiId: apiId,
      apiRef: apiRef,
    );
  }

  factory InterfaceConfigApiBundle.fromJson(Map<String, dynamic> json) =>
      _$InterfaceConfigApiBundleFromJson(json);
}

@freezed
abstract class InterfaceWindowLayoutSectionBundle
    with _$InterfaceWindowLayoutSectionBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWindowLayoutSectionBundle.def({
    @UuidValueConverter() required UuidValue layoutConfigSectionConfigId,
    required String key,
  }) = _InterfaceWindowLayoutSectionBundle;

  factory InterfaceWindowLayoutSectionBundle({
    required UuidValue layoutConfigSectionConfigId,
    required String key,
  }) {
    return _InterfaceWindowLayoutSectionBundle(
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
      key: key,
    );
  }

  factory InterfaceWindowLayoutSectionBundle.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWindowLayoutSectionBundleFromJson(json);
}

@freezed
abstract class InterfaceWindowConfigLayoutBundle
    with _$InterfaceWindowConfigLayoutBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWindowConfigLayoutBundle.def({
    @UuidValueConverter() required UuidValue windowConfigLayoutConfigId,
    @UuidValueConverter() required UuidValue layoutConfigId,
    required String key,
    @Default(const []) List<InterfaceWindowLayoutSectionBundle> sections,
  }) = _InterfaceWindowConfigLayoutBundle;

  factory InterfaceWindowConfigLayoutBundle({
    required UuidValue windowConfigLayoutConfigId,
    required UuidValue layoutConfigId,
    required String key,
    List<InterfaceWindowLayoutSectionBundle> sections = const [],
  }) {
    return _InterfaceWindowConfigLayoutBundle(
      windowConfigLayoutConfigId: windowConfigLayoutConfigId,
      layoutConfigId: layoutConfigId,
      key: key,
      sections: sections,
    );
  }

  factory InterfaceWindowConfigLayoutBundle.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfaceWindowConfigLayoutBundleFromJson(json);
}

@freezed
abstract class InterfaceWindowConfigBundle with _$InterfaceWindowConfigBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceWindowConfigBundle.def({
    @UuidValueConverter() required UuidValue interfaceConfigWindowConfigId,
    @UuidValueConverter() required UuidValue windowConfigId,
    required String key,
    String? description,
    @Default(const []) List<InterfaceWindowConfigLayoutBundle> layoutConfigs,
  }) = _InterfaceWindowConfigBundle;

  factory InterfaceWindowConfigBundle({
    required UuidValue interfaceConfigWindowConfigId,
    required UuidValue windowConfigId,
    required String key,
    String? description,
    List<InterfaceWindowConfigLayoutBundle> layoutConfigs = const [],
  }) {
    return _InterfaceWindowConfigBundle(
      interfaceConfigWindowConfigId: interfaceConfigWindowConfigId,
      windowConfigId: windowConfigId,
      key: key,
      description: description,
      layoutConfigs: layoutConfigs,
    );
  }

  factory InterfaceWindowConfigBundle.fromJson(Map<String, dynamic> json) =>
      _$InterfaceWindowConfigBundleFromJson(json);
}

@freezed
abstract class InterfacePaneSectionMountBundle
    with _$InterfacePaneSectionMountBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfacePaneSectionMountBundle.def({
    @UuidValueConverter() required UuidValue mountId,
    @UuidValueConverter() required UuidValue layoutConfigSectionConfigId,
  }) = _InterfacePaneSectionMountBundle;

  factory InterfacePaneSectionMountBundle({
    required UuidValue mountId,
    required UuidValue layoutConfigSectionConfigId,
  }) {
    return _InterfacePaneSectionMountBundle(
      mountId: mountId,
      layoutConfigSectionConfigId: layoutConfigSectionConfigId,
    );
  }

  factory InterfacePaneSectionMountBundle.fromJson(Map<String, dynamic> json) =>
      _$InterfacePaneSectionMountBundleFromJson(json);
}

@freezed
abstract class InterfacePaneViewInvocationActionBundle
    with _$InterfacePaneViewInvocationActionBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfacePaneViewInvocationActionBundle.def({
    @UuidValueConverter()
    required UuidValue projectionExperienceViewInvocationActionId,
    required String actionKey,
    required String actionKind,
    required String targetRef,
    @UuidValueConverter() UuidValue? apiCapabilityEndpointId,
    @UuidValueConverter() UuidValue? sdkOperationId,
    String? label,
    String? receiptPolicy,
    String? confirmationPolicy,
    String? optimisticPolicy,
  }) = _InterfacePaneViewInvocationActionBundle;

  factory InterfacePaneViewInvocationActionBundle({
    required UuidValue projectionExperienceViewInvocationActionId,
    required String actionKey,
    required String actionKind,
    required String targetRef,
    UuidValue? apiCapabilityEndpointId,
    UuidValue? sdkOperationId,
    String? label,
    String? receiptPolicy,
    String? confirmationPolicy,
    String? optimisticPolicy,
  }) {
    return _InterfacePaneViewInvocationActionBundle(
      projectionExperienceViewInvocationActionId:
          projectionExperienceViewInvocationActionId,
      actionKey: actionKey,
      actionKind: actionKind,
      targetRef: targetRef,
      apiCapabilityEndpointId: apiCapabilityEndpointId,
      sdkOperationId: sdkOperationId,
      label: label,
      receiptPolicy: receiptPolicy,
      confirmationPolicy: confirmationPolicy,
      optimisticPolicy: optimisticPolicy,
    );
  }

  factory InterfacePaneViewInvocationActionBundle.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfacePaneViewInvocationActionBundleFromJson(json);
}

@freezed
abstract class InterfacePaneProjectionExperienceViewBundle
    with _$InterfacePaneProjectionExperienceViewBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfacePaneProjectionExperienceViewBundle.def({
    @UuidValueConverter() required UuidValue bindingId,
    @UuidValueConverter() required UuidValue projectionExperienceViewId,
    @UuidValueConverter() UuidValue? objectProjectionGraphObservableId,
    @UuidValueConverter() UuidValue? projectionExperienceGraphIdentityId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    String? sectionGraphBindingKey,
    @UuidValueConverter() UuidValue? stateModelId,
    required String viewRef,
    String? projectionViewKey,
    required bool isDefault,
    @Default(const [])
    List<InterfacePaneViewInvocationActionBundle> invocationActions,
    @Default(const []) List<InterfacePaneSectionMountBundle> sectionMounts,
  }) = _InterfacePaneProjectionExperienceViewBundle;

  factory InterfacePaneProjectionExperienceViewBundle({
    required UuidValue bindingId,
    required UuidValue projectionExperienceViewId,
    UuidValue? objectProjectionGraphObservableId,
    UuidValue? projectionExperienceGraphIdentityId,
    UuidValue? objectProjectionGraphIdentityId,
    String? sectionGraphBindingKey,
    UuidValue? stateModelId,
    required String viewRef,
    String? projectionViewKey,
    bool? isDefault,
    List<InterfacePaneViewInvocationActionBundle> invocationActions = const [],
    List<InterfacePaneSectionMountBundle> sectionMounts = const [],
  }) {
    return _InterfacePaneProjectionExperienceViewBundle(
      bindingId: bindingId,
      projectionExperienceViewId: projectionExperienceViewId,
      objectProjectionGraphObservableId: objectProjectionGraphObservableId,
      projectionExperienceGraphIdentityId: projectionExperienceGraphIdentityId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      sectionGraphBindingKey: sectionGraphBindingKey,
      stateModelId: stateModelId,
      viewRef: viewRef,
      projectionViewKey: projectionViewKey,
      isDefault: isDefault ?? false,
      invocationActions: invocationActions,
      sectionMounts: sectionMounts,
    );
  }

  factory InterfacePaneProjectionExperienceViewBundle.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfacePaneProjectionExperienceViewBundleFromJson({
    ...json,
    if (!json.containsKey('is_default')) 'is_default': false,
  });
}

@freezed
abstract class InterfacePaneApiCapabilityEndpointBundle
    with _$InterfacePaneApiCapabilityEndpointBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfacePaneApiCapabilityEndpointBundle.def({
    @UuidValueConverter() required UuidValue bindingId,
    @UuidValueConverter() required UuidValue apiCapabilityEndpointId,
    String? endpointRef,
    String? discriminant,
  }) = _InterfacePaneApiCapabilityEndpointBundle;

  factory InterfacePaneApiCapabilityEndpointBundle({
    required UuidValue bindingId,
    required UuidValue apiCapabilityEndpointId,
    String? endpointRef,
    String? discriminant,
  }) {
    return _InterfacePaneApiCapabilityEndpointBundle(
      bindingId: bindingId,
      apiCapabilityEndpointId: apiCapabilityEndpointId,
      endpointRef: endpointRef,
      discriminant: discriminant,
    );
  }

  factory InterfacePaneApiCapabilityEndpointBundle.fromJson(
    Map<String, dynamic> json,
  ) => _$InterfacePaneApiCapabilityEndpointBundleFromJson(json);
}

@freezed
abstract class InterfacePaneSdkOperationBundle
    with _$InterfacePaneSdkOperationBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfacePaneSdkOperationBundle.def({
    @UuidValueConverter() required UuidValue bindingId,
    @UuidValueConverter() required UuidValue sdkOperationId,
    String? operationRef,
    String? discriminant,
  }) = _InterfacePaneSdkOperationBundle;

  factory InterfacePaneSdkOperationBundle({
    required UuidValue bindingId,
    required UuidValue sdkOperationId,
    String? operationRef,
    String? discriminant,
  }) {
    return _InterfacePaneSdkOperationBundle(
      bindingId: bindingId,
      sdkOperationId: sdkOperationId,
      operationRef: operationRef,
      discriminant: discriminant,
    );
  }

  factory InterfacePaneSdkOperationBundle.fromJson(Map<String, dynamic> json) =>
      _$InterfacePaneSdkOperationBundleFromJson(json);
}

@freezed
abstract class InterfacePaneConfigBundle with _$InterfacePaneConfigBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfacePaneConfigBundle.def({
    @UuidValueConverter() required UuidValue paneConfigId,
    @UuidValueConverter() UuidValue? panePackageId,
    String? panePackageName,
    required String name,
    required String paneKind,
    String? description,
    String? narrativeKey,
    @Default(const [])
    List<InterfacePaneProjectionExperienceViewBundle> projectionExperienceViews,
    @Default(const [])
    List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints,
    @Default(const []) List<InterfacePaneSdkOperationBundle> sdkOperations,
  }) = _InterfacePaneConfigBundle;

  factory InterfacePaneConfigBundle({
    required UuidValue paneConfigId,
    UuidValue? panePackageId,
    String? panePackageName,
    required String name,
    required String paneKind,
    String? description,
    String? narrativeKey,
    List<InterfacePaneProjectionExperienceViewBundle>
        projectionExperienceViews =
        const [],
    List<InterfacePaneApiCapabilityEndpointBundle> apiCapabilityEndpoints =
        const [],
    List<InterfacePaneSdkOperationBundle> sdkOperations = const [],
  }) {
    return _InterfacePaneConfigBundle(
      paneConfigId: paneConfigId,
      panePackageId: panePackageId,
      panePackageName: panePackageName,
      name: name,
      paneKind: paneKind,
      description: description,
      narrativeKey: narrativeKey,
      projectionExperienceViews: projectionExperienceViews,
      apiCapabilityEndpoints: apiCapabilityEndpoints,
      sdkOperations: sdkOperations,
    );
  }

  factory InterfacePaneConfigBundle.fromJson(Map<String, dynamic> json) =>
      _$InterfacePaneConfigBundleFromJson(json);
}

@freezed
abstract class InterfaceConfigBundle with _$InterfaceConfigBundle {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory InterfaceConfigBundle.def({
    @UuidValueConverter() required UuidValue interfacePackageId,
    required String interfacePackageName,
    @UuidValueConverter() required UuidValue interfaceConfigId,
    required String name,
    String? description,
    @Default(const []) List<InterfaceConfigApiBundle> apis,
    @Default(const []) List<InterfaceWindowConfigBundle> windowConfigs,
    @Default(const []) List<InterfacePaneConfigBundle> paneConfigs,
  }) = _InterfaceConfigBundle;

  factory InterfaceConfigBundle({
    required UuidValue interfacePackageId,
    required String interfacePackageName,
    required UuidValue interfaceConfigId,
    required String name,
    String? description,
    List<InterfaceConfigApiBundle> apis = const [],
    List<InterfaceWindowConfigBundle> windowConfigs = const [],
    List<InterfacePaneConfigBundle> paneConfigs = const [],
  }) {
    return _InterfaceConfigBundle(
      interfacePackageId: interfacePackageId,
      interfacePackageName: interfacePackageName,
      interfaceConfigId: interfaceConfigId,
      name: name,
      description: description,
      apis: apis,
      windowConfigs: windowConfigs,
      paneConfigs: paneConfigs,
    );
  }

  factory InterfaceConfigBundle.fromJson(Map<String, dynamic> json) =>
      _$InterfaceConfigBundleFromJson(json);
}
