import 'package:aware_api/aware_api.dart';
import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid_value.dart';

import '../render_spec/pane_render_spec.dart';
import '../render_spec/render_component_registry.dart';
import 'interface_view_state_decoder_registry.dart';

const String kInterfacePackageRuntimeSourceStaticDartRegistry =
    'static_dart_registry';
const String kInterfacePackageRuntimeSourceUnknown = 'unknown';

@immutable
class InterfacePackageRuntimeLayout {
  const InterfacePackageRuntimeLayout({
    required this.layoutConfigId,
    required this.layoutKey,
    required this.label,
    this.isDefault = false,
  });

  final String layoutConfigId;
  final String layoutKey;
  final String label;
  final bool isDefault;
}

@immutable
class InterfacePackageRuntimeSectionRepresentation {
  const InterfacePackageRuntimeSectionRepresentation({
    required this.representationId,
    required this.windowKey,
    required this.layoutKey,
    required this.sectionKey,
    required this.paneName,
    required this.paneKind,
    required this.label,
    required this.observableId,
    required this.viewRef,
    required this.projectionViewKey,
  });

  final String representationId;
  final String windowKey;
  final String layoutKey;
  final String sectionKey;
  final String paneName;
  final String paneKind;
  final String label;
  final String observableId;
  final String viewRef;
  final String projectionViewKey;
}

@immutable
class InterfacePackageRuntimeApiPackage {
  const InterfacePackageRuntimeApiPackage({
    required this.apiPackageId,
    required this.apiPackageName,
  });

  final String apiPackageId;
  final String apiPackageName;
}

@immutable
class InterfacePackageRuntimeApi {
  const InterfacePackageRuntimeApi({
    required this.interfaceName,
    required this.interfaceConfigId,
    required this.interfaceConfigApiId,
    required this.apiId,
    required this.apiRef,
  });

  final String interfaceName;
  final String interfaceConfigId;
  final String interfaceConfigApiId;
  final String apiId;
  final String apiRef;
}

typedef InterfacePackageRuntimeApiClientFactory = Object Function(
    AwareApiClient client);

@immutable
class InterfacePackageRuntimeApiClientFactoryRegistration {
  const InterfacePackageRuntimeApiClientFactoryRegistration({
    required this.apiPackageId,
    required this.apiPackageName,
    required this.clientTypeName,
    required this.buildClient,
  });

  final String apiPackageId;
  final String apiPackageName;
  final String clientTypeName;
  final InterfacePackageRuntimeApiClientFactory buildClient;
}

@immutable
class InterfacePackageRuntime {
  const InterfacePackageRuntime({
    required this.interfacePackageId,
    required this.interfacePackageName,
    required this.panePackageRegistry,
    this.sourceKind = kInterfacePackageRuntimeSourceStaticDartRegistry,
    this.apiPackages = const <InterfacePackageRuntimeApiPackage>[],
    this.apiClientFactories =
        const <InterfacePackageRuntimeApiClientFactoryRegistration>[],
    this.apis = const <InterfacePackageRuntimeApi>[],
    this.experienceKeys = const <String>[],
    this.layouts = const <InterfacePackageRuntimeLayout>[],
    this.sectionRepresentations =
        const <InterfacePackageRuntimeSectionRepresentation>[],
    this.renderSpecs = const <PaneRenderSpec>[],
    this.renderComponentRegistry = const RenderComponentRegistry.empty(),
    this.viewStateDecoderRegistry =
        const InterfaceViewStateDecoderRegistry.empty(),
  });

  factory InterfacePackageRuntime.fromRuntimePackageState(
    InterfaceRuntimePackageState state, {
    PanePackageRegistry? panePackageRegistry,
    RenderComponentRegistry? renderComponentRegistry,
    InterfaceViewStateDecoderRegistry? viewStateDecoderRegistry,
  }) {
    final packageName = state.interfacePackageName.trim();
    if (packageName.isEmpty) {
      throw ArgumentError.value(
        state.interfacePackageName,
        'state.interfacePackageName',
        'must be non-empty',
      );
    }
    final packageId = _uuidString(state.interfacePackageId) ?? packageName;
    return InterfacePackageRuntime(
      sourceKind: _normalizeSourceKind(state.sourceKind),
      interfacePackageId: packageId,
      interfacePackageName: packageName,
      panePackageRegistry: panePackageRegistry ?? PanePackageRegistry(),
      apiPackages: <InterfacePackageRuntimeApiPackage>[
        for (final apiPackage in state.apiPackages)
          InterfacePackageRuntimeApiPackage(
            apiPackageId: _uuidString(apiPackage.apiPackageId) ??
                apiPackage.apiPackageName,
            apiPackageName: apiPackage.apiPackageName,
          ),
      ],
      apis: state.apis
          .map((api) => _runtimeApiFromState(api, packageName))
          .whereType<InterfacePackageRuntimeApi>()
          .toList(growable: false),
      experienceKeys: List<String>.unmodifiable(
        state.experienceKeys.where((key) => key.trim().isNotEmpty),
      ),
      layouts: <InterfacePackageRuntimeLayout>[
        for (final layout in state.layouts)
          InterfacePackageRuntimeLayout(
            layoutConfigId:
                _uuidString(layout.layoutConfigId) ?? layout.layoutKey,
            layoutKey: layout.layoutKey,
            label: layout.label,
            isDefault: layout.isDefault,
          ),
      ],
      sectionRepresentations: <InterfacePackageRuntimeSectionRepresentation>[
        for (final representation in state.sectionRepresentations)
          InterfacePackageRuntimeSectionRepresentation(
            representationId: representation.representationId.uuid,
            windowKey: representation.windowKey,
            layoutKey: representation.layoutKey,
            sectionKey: representation.sectionKey,
            paneName: representation.paneName,
            paneKind: representation.paneKind,
            label: representation.label,
            observableId: representation.observableId.uuid,
            viewRef: representation.viewRef,
            projectionViewKey: representation.projectionViewKey ?? '',
          ),
      ],
      renderSpecs: paneRenderSpecsFromRuntimePaneRenderSpecStates(
        state.dynamicPaneRenderSpecs,
      ),
      renderComponentRegistry:
          renderComponentRegistry ?? const RenderComponentRegistry.empty(),
      viewStateDecoderRegistry: viewStateDecoderRegistry ??
          const InterfaceViewStateDecoderRegistry.empty(),
    );
  }

  final String interfacePackageId;
  final String interfacePackageName;
  final String sourceKind;
  final PanePackageRegistry panePackageRegistry;
  final List<InterfacePackageRuntimeApiPackage> apiPackages;
  final List<InterfacePackageRuntimeApiClientFactoryRegistration>
      apiClientFactories;
  final List<InterfacePackageRuntimeApi> apis;
  final List<String> experienceKeys;
  final List<InterfacePackageRuntimeLayout> layouts;
  final List<InterfacePackageRuntimeSectionRepresentation>
      sectionRepresentations;
  final List<PaneRenderSpec> renderSpecs;
  final RenderComponentRegistry renderComponentRegistry;
  final InterfaceViewStateDecoderRegistry viewStateDecoderRegistry;

  InterfacePackageRuntimeApiClientFactoryRegistration? resolveApiClientFactory({
    String? apiPackageId,
    String? apiPackageName,
  }) {
    final normalizedApiPackageId = apiPackageId?.trim();
    if (normalizedApiPackageId != null && normalizedApiPackageId.isNotEmpty) {
      for (final registration in apiClientFactories) {
        if (registration.apiPackageId == normalizedApiPackageId) {
          return registration;
        }
      }
    }
    final normalizedApiPackageName = apiPackageName?.trim();
    if (normalizedApiPackageName == null || normalizedApiPackageName.isEmpty) {
      return null;
    }
    for (final registration in apiClientFactories) {
      if (registration.apiPackageName == normalizedApiPackageName) {
        return registration;
      }
    }
    return null;
  }

  Object buildApiClient({
    required AwareApiClient client,
    String? apiPackageId,
    String? apiPackageName,
  }) {
    final registration = resolveApiClientFactory(
      apiPackageId: apiPackageId,
      apiPackageName: apiPackageName,
    );
    if (registration == null) {
      throw StateError(
        'InterfacePackageRuntime has no API client factory for '
        'apiPackageId=${apiPackageId ?? "<unset>"} '
        'apiPackageName=${apiPackageName ?? "<unset>"}.',
      );
    }
    return registration.buildClient(client);
  }

  InterfacePackageRuntime withRenderSpecOverlay(
    List<PaneRenderSpec> overlayRenderSpecs,
  ) {
    if (overlayRenderSpecs.isEmpty) {
      return this;
    }
    final overlayIds = overlayRenderSpecs
        .map((spec) => spec.specId.trim())
        .where((specId) => specId.isNotEmpty)
        .toSet();
    return InterfacePackageRuntime(
      sourceKind: sourceKind,
      interfacePackageId: interfacePackageId,
      interfacePackageName: interfacePackageName,
      panePackageRegistry: panePackageRegistry,
      apiPackages: apiPackages,
      apiClientFactories: apiClientFactories,
      apis: apis,
      experienceKeys: experienceKeys,
      layouts: layouts,
      sectionRepresentations: sectionRepresentations,
      renderSpecs: List<PaneRenderSpec>.unmodifiable(<PaneRenderSpec>[
        ...overlayRenderSpecs,
        for (final spec in renderSpecs)
          if (!overlayIds.contains(spec.specId.trim())) spec,
      ]),
      renderComponentRegistry: renderComponentRegistry,
      viewStateDecoderRegistry: viewStateDecoderRegistry,
    );
  }

  InterfacePackageRuntime withStaticRuntimeAccelerator(
    InterfacePackageRuntime accelerator,
  ) {
    final hasPanePackages =
        panePackageRegistry.registeredPanePackageIds().isNotEmpty;
    return InterfacePackageRuntime(
      sourceKind: sourceKind,
      interfacePackageId: interfacePackageId,
      interfacePackageName: interfacePackageName,
      panePackageRegistry: hasPanePackages
          ? panePackageRegistry
          : accelerator.panePackageRegistry,
      apiPackages:
          apiPackages.isNotEmpty ? apiPackages : accelerator.apiPackages,
      apiClientFactories: accelerator.apiClientFactories,
      apis: apis.isNotEmpty ? apis : accelerator.apis,
      experienceKeys: _mergeRuntimeStrings(
        experienceKeys,
        accelerator.experienceKeys,
      ),
      layouts: layouts.isNotEmpty ? layouts : accelerator.layouts,
      sectionRepresentations: sectionRepresentations.isNotEmpty
          ? sectionRepresentations
          : accelerator.sectionRepresentations,
      renderSpecs: _mergeRenderSpecs(renderSpecs, accelerator.renderSpecs),
      renderComponentRegistry: renderComponentRegistry.isEmpty
          ? accelerator.renderComponentRegistry
          : renderComponentRegistry,
      viewStateDecoderRegistry: viewStateDecoderRegistry.isEmpty
          ? accelerator.viewStateDecoderRegistry
          : viewStateDecoderRegistry,
    );
  }

  List<InterfacePackageRuntimeSectionRepresentation>
      resolveSectionRepresentations({
    String? windowKey,
    String? layoutKey,
    String? sectionKey,
  }) {
    final normalizedWindowKey = _normalizeRuntimeValue(windowKey);
    final normalizedLayoutKey = _normalizeRuntimeValue(layoutKey);
    final normalizedSectionKey = _normalizeRuntimeValue(sectionKey);
    return List<InterfacePackageRuntimeSectionRepresentation>.unmodifiable(
      sectionRepresentations.where((representation) {
        if (normalizedWindowKey != null &&
            representation.windowKey.trim().toLowerCase() !=
                normalizedWindowKey) {
          return false;
        }
        if (normalizedLayoutKey != null &&
            representation.layoutKey.trim().toLowerCase() !=
                normalizedLayoutKey) {
          return false;
        }
        if (normalizedSectionKey != null &&
            representation.sectionKey.trim().toLowerCase() !=
                normalizedSectionKey) {
          return false;
        }
        return true;
      }),
    );
  }

  List<InterfacePackageRuntimeLayout> resolveLayouts({
    String? layoutConfigId,
    String? layoutKey,
  }) {
    final normalizedLayoutConfigId = _normalizeRuntimeValue(layoutConfigId);
    final normalizedLayoutKey = _normalizeRuntimeValue(layoutKey);
    return List<InterfacePackageRuntimeLayout>.unmodifiable(
      layouts.where((layout) {
        if (normalizedLayoutConfigId != null &&
            layout.layoutConfigId.trim().toLowerCase() !=
                normalizedLayoutConfigId) {
          return false;
        }
        if (normalizedLayoutKey != null &&
            layout.layoutKey.trim().toLowerCase() != normalizedLayoutKey) {
          return false;
        }
        return true;
      }),
    );
  }
}

class InterfacePackageRuntimeRegistry {
  InterfacePackageRuntimeRegistry();

  final Map<String, InterfacePackageRuntime> _byInterfacePackageId =
      <String, InterfacePackageRuntime>{};
  final Map<String, InterfacePackageRuntime> _byInterfacePackageName =
      <String, InterfacePackageRuntime>{};
  final Map<String, InterfacePackageRuntime> _byExperienceKey =
      <String, InterfacePackageRuntime>{};

  void register(InterfacePackageRuntime runtime) {
    final interfacePackageId = runtime.interfacePackageId.trim();
    if (interfacePackageId.isEmpty) {
      throw ArgumentError.value(
        runtime.interfacePackageId,
        'runtime.interfacePackageId',
        'must be non-empty',
      );
    }
    _byInterfacePackageId[interfacePackageId] = runtime;
    final interfacePackageName = _normalizeRuntimeValue(
      runtime.interfacePackageName,
    );
    if (interfacePackageName != null) {
      _byInterfacePackageName[interfacePackageName] = runtime;
    }
    for (final experienceKey in runtime.experienceKeys) {
      final normalized = experienceKey.trim();
      if (normalized.isEmpty) {
        continue;
      }
      _byExperienceKey[normalized] = runtime;
    }
  }

  InterfacePackageRuntime? resolve({
    String? interfacePackageId,
    String? interfacePackageName,
    String? experienceKey,
  }) {
    final normalizedInterfacePackageId = interfacePackageId?.trim();
    if (normalizedInterfacePackageId != null &&
        normalizedInterfacePackageId.isNotEmpty) {
      final byId = _byInterfacePackageId[normalizedInterfacePackageId];
      if (byId != null) {
        return byId;
      }
    }
    final normalizedInterfacePackageName = _normalizeRuntimeValue(
      interfacePackageName,
    );
    if (normalizedInterfacePackageName != null) {
      final byName = _byInterfacePackageName[normalizedInterfacePackageName];
      if (byName != null) {
        return byName;
      }
    }
    final normalizedExperienceKey = experienceKey?.trim();
    if (normalizedExperienceKey == null || normalizedExperienceKey.isEmpty) {
      return null;
    }
    return _byExperienceKey[normalizedExperienceKey];
  }

  List<String> registeredInterfacePackageIds() {
    return _byInterfacePackageId.keys.toList(growable: false);
  }

  InterfacePackageRuntimeApiClientFactoryRegistration? resolveApiClientFactory({
    String? interfacePackageId,
    String? experienceKey,
    String? apiPackageId,
    String? apiPackageName,
  }) {
    final runtime = resolve(
      interfacePackageId: interfacePackageId,
      experienceKey: experienceKey,
    );
    return runtime?.resolveApiClientFactory(
      apiPackageId: apiPackageId,
      apiPackageName: apiPackageName,
    );
  }
}

String? _normalizeRuntimeValue(String? value) {
  final normalized = value?.trim().toLowerCase();
  return normalized == null || normalized.isEmpty ? null : normalized;
}

String _normalizeSourceKind(String? value) {
  final normalized = value?.trim();
  return normalized == null || normalized.isEmpty
      ? kInterfacePackageRuntimeSourceUnknown
      : normalized;
}

String? _uuidString(UuidValue? value) {
  final text = value?.uuid.trim();
  return text == null || text.isEmpty ? null : text;
}

List<String> _mergeRuntimeStrings(
  Iterable<String> primary,
  Iterable<String> secondary,
) {
  final values = <String>[];
  final seen = <String>{};
  for (final value in <String>[...primary, ...secondary]) {
    final trimmed = value.trim();
    if (trimmed.isEmpty || !seen.add(trimmed)) {
      continue;
    }
    values.add(trimmed);
  }
  return List<String>.unmodifiable(values);
}

List<PaneRenderSpec> _mergeRenderSpecs(
  Iterable<PaneRenderSpec> primary,
  Iterable<PaneRenderSpec> secondary,
) {
  final specs = <PaneRenderSpec>[];
  final seen = <String>{};
  for (final spec in <PaneRenderSpec>[...primary, ...secondary]) {
    final specId = spec.specId.trim();
    final key = specId.isEmpty
        ? '${spec.paneKind}|${spec.viewRef}|${spec.projectionViewKey}|${specs.length}'
        : specId;
    if (!seen.add(key)) {
      continue;
    }
    specs.add(spec);
  }
  return List<PaneRenderSpec>.unmodifiable(specs);
}

InterfacePackageRuntimeApi? _runtimeApiFromState(
  InterfaceRuntimePackageApiState state,
  String fallbackInterfaceName,
) {
  final interfaceConfigId = _uuidString(state.interfaceConfigId);
  final interfaceConfigApiId = _uuidString(state.interfaceConfigApiId);
  final apiId = _uuidString(state.apiId);
  final apiRef = state.apiRef.trim();
  if (interfaceConfigId == null ||
      interfaceConfigApiId == null ||
      apiId == null ||
      apiRef.isEmpty) {
    return null;
  }
  return InterfacePackageRuntimeApi(
    interfaceName: state.interfaceName?.trim().isNotEmpty == true
        ? state.interfaceName!.trim()
        : fallbackInterfaceName,
    interfaceConfigId: interfaceConfigId,
    interfaceConfigApiId: interfaceConfigApiId,
    apiId: apiId,
    apiRef: apiRef,
  );
}
