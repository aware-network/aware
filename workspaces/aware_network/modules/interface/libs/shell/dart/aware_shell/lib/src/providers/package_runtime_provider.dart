import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'host_state_provider.dart';
import '../render_spec/pane_render_spec.dart';
import '../runtime/interface_package_runtime.dart';

final interfacePackageRuntimeRegistryProvider =
    Provider<InterfacePackageRuntimeRegistry>((ref) {
  return InterfacePackageRuntimeRegistry();
});

final currentInterfacePackageRuntimeProvider =
    Provider<InterfacePackageRuntime?>(
  dependencies: <ProviderOrFamily>[
    interfacePackageRuntimeRegistryProvider,
    interfaceHostStateProvider,
  ],
  (ref) {
    final registry = ref.watch(interfacePackageRuntimeRegistryProvider);
    final hostState = ref.watch(interfaceHostStateProvider).valueOrNull;
    return resolveInterfacePackageRuntimeForHostState(
      registry: registry,
      hostState: hostState,
    );
  },
);

enum InterfacePackageRuntimeReadinessStatus { unavailable, ready, incompatible }

@immutable
class InterfacePackageRuntimeReadiness {
  const InterfacePackageRuntimeReadiness({
    required this.status,
    required this.title,
    required this.message,
    this.interfacePackageRuntime,
    this.issues = const <String>[],
  });

  final InterfacePackageRuntimeReadinessStatus status;
  final String title;
  final String message;
  final InterfacePackageRuntime? interfacePackageRuntime;
  final List<String> issues;

  bool get ready => status == InterfacePackageRuntimeReadinessStatus.ready;

  bool get blocksRuntimeShell =>
      status == InterfacePackageRuntimeReadinessStatus.incompatible;
}

final currentInterfacePackageRuntimeReadinessProvider =
    Provider<InterfacePackageRuntimeReadiness>(
  dependencies: <ProviderOrFamily>[
    interfacePackageRuntimeRegistryProvider,
    interfaceHostStateProvider,
  ],
  (ref) {
    final registry = ref.watch(interfacePackageRuntimeRegistryProvider);
    final hostState = ref.watch(interfaceHostStateProvider).valueOrNull;
    return resolveInterfacePackageRuntimeReadiness(
      registry: registry,
      hostState: hostState,
    );
  },
);

@immutable
class InterfaceRuntimeLayoutCatalogOption {
  const InterfaceRuntimeLayoutCatalogOption({
    required this.layout,
    required this.isActive,
  });

  final InterfacePackageRuntimeLayout layout;
  final bool isActive;
}

@immutable
class InterfaceRuntimeLayoutCatalog {
  const InterfaceRuntimeLayoutCatalog({
    this.options = const <InterfaceRuntimeLayoutCatalogOption>[],
    this.activeLayoutConfigId,
    this.activeLayoutKey,
    this.errorMessage,
    this.errorDetail,
  });

  final List<InterfaceRuntimeLayoutCatalogOption> options;
  final String? activeLayoutConfigId;
  final String? activeLayoutKey;
  final String? errorMessage;
  final String? errorDetail;

  bool get hasError => errorMessage?.trim().isNotEmpty == true;

  InterfaceRuntimeLayoutCatalogOption? resolveLayout({
    String? layoutConfigId,
    String? layoutKey,
  }) {
    final normalizedLayoutConfigId = _normalizeSelectionValue(layoutConfigId);
    final normalizedLayoutKey = _normalizeSelectionValue(layoutKey);
    for (final option in options) {
      if (normalizedLayoutConfigId != null &&
          _normalizeSelectionValue(option.layout.layoutConfigId) ==
              normalizedLayoutConfigId) {
        return option;
      }
      if (normalizedLayoutConfigId == null &&
          normalizedLayoutKey != null &&
          _normalizeSelectionValue(option.layout.layoutKey) ==
              normalizedLayoutKey) {
        return option;
      }
    }
    return null;
  }
}

final currentInterfaceLayoutCatalogProvider =
    Provider<InterfaceRuntimeLayoutCatalog>(
  dependencies: <ProviderOrFamily>[
    interfacePackageRuntimeRegistryProvider,
    interfaceHostStateProvider,
    currentInterfacePackageRuntimeProvider,
  ],
  (ref) {
    final hostState = ref.watch(interfaceHostStateProvider).valueOrNull;
    final interfacePackageRuntime = ref.watch(
      currentInterfacePackageRuntimeProvider,
    );
    return resolveInterfaceRuntimeLayoutCatalog(
      hostState: hostState,
      interfacePackageRuntime: interfacePackageRuntime,
    );
  },
);

@immutable
class InterfaceRuntimeSectionRepresentationOption {
  const InterfaceRuntimeSectionRepresentationOption({
    required this.representation,
    required this.isActive,
  });

  final InterfacePackageRuntimeSectionRepresentation representation;
  final bool isActive;
}

@immutable
class InterfaceRuntimeSectionRepresentationResolution {
  const InterfaceRuntimeSectionRepresentationResolution({
    this.options = const <InterfaceRuntimeSectionRepresentationOption>[],
    this.layoutKey,
    this.sectionKey,
    this.errorMessage,
    this.errorDetail,
  });

  final List<InterfaceRuntimeSectionRepresentationOption> options;
  final String? layoutKey;
  final String? sectionKey;
  final String? errorMessage;
  final String? errorDetail;

  bool get hasError => errorMessage?.trim().isNotEmpty == true;
}

@immutable
class InterfaceRuntimeSectionRepresentationCatalog {
  const InterfaceRuntimeSectionRepresentationCatalog({
    this.layoutKey,
    this.activeSectionKey,
    this.sectionKeys = const <String>[],
    this.sections =
        const <String, InterfaceRuntimeSectionRepresentationResolution>{},
    this.errorMessage,
    this.errorDetail,
  });

  final String? layoutKey;
  final String? activeSectionKey;
  final List<String> sectionKeys;
  final Map<String, InterfaceRuntimeSectionRepresentationResolution> sections;
  final String? errorMessage;
  final String? errorDetail;

  bool get hasError => errorMessage?.trim().isNotEmpty == true;

  InterfaceRuntimeSectionRepresentationResolution resolveSection(
    String? sectionKey,
  ) {
    final normalizedSectionKey = _normalizeSelectionValue(sectionKey);
    if (hasError) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: layoutKey,
        sectionKey: normalizedSectionKey ?? activeSectionKey,
        errorMessage: errorMessage,
        errorDetail: errorDetail,
      );
    }

    final resolvedSectionKey = normalizedSectionKey ??
        activeSectionKey ??
        (sectionKeys.length == 1 ? sectionKeys.first : null);
    if (resolvedSectionKey == null) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: layoutKey,
        errorMessage:
            'Aware Shell did not expose an active mounted section selection.',
        errorDetail: sectionKeys.join(', '),
      );
    }

    return sections[resolvedSectionKey] ??
        InterfaceRuntimeSectionRepresentationResolution(
          layoutKey: layoutKey,
          sectionKey: resolvedSectionKey,
          errorMessage:
              'The compiled interface package does not declare section representations for the requested mounted section.',
          errorDetail: resolvedSectionKey,
        );
  }

  InterfaceRuntimeSectionRepresentationOption? resolveRepresentation(
    String representationId,
  ) {
    final normalizedRepresentationId = _normalizeSelectionValue(
      representationId,
    );
    if (normalizedRepresentationId == null) {
      return null;
    }
    for (final sectionKey in sectionKeys) {
      final resolution = sections[sectionKey];
      if (resolution == null || resolution.hasError) {
        continue;
      }
      for (final option in resolution.options) {
        if (_normalizeSelectionValue(option.representation.representationId) ==
            normalizedRepresentationId) {
          return option;
        }
      }
    }
    return null;
  }

  List<InterfaceRuntimeSectionRepresentationOption> resolvePaneRepresentations(
    String paneKey, {
    String? sectionKey,
  }) {
    final resolution = resolveSection(sectionKey);
    if (resolution.hasError) {
      return const <InterfaceRuntimeSectionRepresentationOption>[];
    }
    final normalizedPaneKey = _normalizeSelectionValue(paneKey);
    if (normalizedPaneKey == null) {
      return const <InterfaceRuntimeSectionRepresentationOption>[];
    }
    return List<InterfaceRuntimeSectionRepresentationOption>.unmodifiable(
      resolution.options.where(
        (option) => _paneRepresentationMatchesKey(
          option.representation,
          normalizedPaneKey,
        ),
      ),
    );
  }

  InterfaceRuntimeSectionRepresentationOption? resolveDefaultPaneRepresentation(
    String paneKey, {
    String? sectionKey,
  }) {
    final options = resolvePaneRepresentations(paneKey, sectionKey: sectionKey);
    if (options.isEmpty) {
      return null;
    }
    for (final option in options) {
      if (option.isActive) {
        return option;
      }
    }
    return options.length == 1 ? options.single : null;
  }
}

final currentInterfaceSectionRepresentationCatalogProvider =
    Provider<InterfaceRuntimeSectionRepresentationCatalog>(
  dependencies: <ProviderOrFamily>[
    interfacePackageRuntimeRegistryProvider,
    interfaceHostStateProvider,
    currentInterfacePackageRuntimeProvider,
  ],
  (ref) {
    final hostState = ref.watch(interfaceHostStateProvider).valueOrNull;
    final interfacePackageRuntime = ref.watch(
      currentInterfacePackageRuntimeProvider,
    );
    return resolveInterfaceRuntimeSectionRepresentationCatalog(
      hostState: hostState,
      interfacePackageRuntime: interfacePackageRuntime,
    );
  },
);

final currentInterfaceSectionRepresentationResolutionProvider =
    Provider.family<InterfaceRuntimeSectionRepresentationResolution, String?>(
  dependencies: <ProviderOrFamily>[
    currentInterfaceSectionRepresentationCatalogProvider,
  ],
  (ref, sectionKey) {
    final catalog = ref.watch(
      currentInterfaceSectionRepresentationCatalogProvider,
    );
    return catalog.resolveSection(sectionKey);
  },
);

InterfacePackageRuntime? resolveInterfacePackageRuntimeForHostState({
  required InterfacePackageRuntimeRegistry registry,
  required InterfaceHostState? hostState,
}) {
  final runtimeState = hostState?.runtime;
  final resolvedView = runtimeState?.resolvedView;
  final hostPackageRuntime = runtimeState?.interfacePackageRuntime == null
      ? null
      : InterfacePackageRuntime.fromRuntimePackageState(
          runtimeState!.interfacePackageRuntime!,
        );
  final staticPackageRuntime = _resolveStaticInterfacePackageRuntime(
    registry: registry,
    resolvedView: resolvedView,
    hostPackageRuntime: hostPackageRuntime,
  );
  final interfacePackageRuntime = hostPackageRuntime == null
      ? staticPackageRuntime
      : (staticPackageRuntime == null
          ? hostPackageRuntime
          : hostPackageRuntime.withStaticRuntimeAccelerator(
              staticPackageRuntime,
            ));
  if (interfacePackageRuntime == null) {
    return null;
  }
  return interfacePackageRuntime.withRenderSpecOverlay(
    paneRenderSpecsFromInterfaceRuntimeState(runtimeState),
  );
}

InterfacePackageRuntimeReadiness resolveInterfacePackageRuntimeReadiness({
  required InterfacePackageRuntimeRegistry registry,
  required InterfaceHostState? hostState,
}) {
  final runtime = hostState?.runtime;
  final resolvedView = runtime?.resolvedView;
  if (runtime == null) {
    return const InterfacePackageRuntimeReadiness(
      status: InterfacePackageRuntimeReadinessStatus.unavailable,
      title: 'Interface Runtime Pending',
      message:
          'Interface Host has not selected a runtime interface package for this namespace yet.',
    );
  }
  if (_runtimeHasHostBootstrapPaneContributions(runtime)) {
    return const InterfacePackageRuntimeReadiness(
      status: InterfacePackageRuntimeReadinessStatus.ready,
      title: 'Interface Bootstrap Ready',
      message:
          'Interface Host is exposing bootstrap pane contributions before a compiled interface package is mounted.',
    );
  }
  if (resolvedView == null) {
    return const InterfacePackageRuntimeReadiness(
      status: InterfacePackageRuntimeReadinessStatus.unavailable,
      title: 'Interface Runtime Pending',
      message:
          'Interface Host has not selected a runtime interface package for this namespace yet.',
    );
  }

  final interfacePackageRuntime = resolveInterfacePackageRuntimeForHostState(
    registry: registry,
    hostState: hostState,
  );
  if (interfacePackageRuntime == null) {
    final hostPackage = _hostInterfacePackageLabel(resolvedView);
    return InterfacePackageRuntimeReadiness(
      status: InterfacePackageRuntimeReadinessStatus.incompatible,
      title: 'Interface Package Runtime Missing',
      message:
          'Interface Host selected $hostPackage, but host state did not include a data-only runtime and this Flutter build does not include a compatible static Dart accelerator.',
      issues: <String>['missing_interface_package_runtime:$hostPackage'],
    );
  }

  final fatalIssues = <String>[
    ..._interfacePackageIdentityIssues(
      resolvedView: resolvedView,
      interfacePackageRuntime: interfacePackageRuntime,
    ),
  ];
  final diagnostics = <String>[
    ...fatalIssues,
    ..._interfaceRuntimeLayoutIssues(
      runtime: runtime,
      interfacePackageRuntime: interfacePackageRuntime,
    ),
    ..._interfaceRuntimeSectionRepresentationIssues(
      runtime: runtime,
      interfacePackageRuntime: interfacePackageRuntime,
    ),
    ..._interfaceRuntimePanePackageIssues(
      runtime: runtime,
      interfacePackageRuntime: interfacePackageRuntime,
    ),
  ];

  if (fatalIssues.isNotEmpty) {
    return InterfacePackageRuntimeReadiness(
      status: InterfacePackageRuntimeReadinessStatus.incompatible,
      title: 'Interface Package Incompatible',
      message:
          'Interface Host selected ${interfacePackageRuntime.interfacePackageName}, but its runtime surface does not match the selected interface package runtime.',
      interfacePackageRuntime: interfacePackageRuntime,
      issues: List<String>.unmodifiable(diagnostics),
    );
  }

  if (runtime.interfacePackageRuntime != null) {
    return InterfacePackageRuntimeReadiness(
      status: InterfacePackageRuntimeReadinessStatus.ready,
      title: 'Interface Runtime Ready',
      message:
          'Interface Host supplied ${interfacePackageRuntime.interfacePackageName} as a data-only runtime. Linked Dart packages are optional renderer accelerators; host-mounted panes resolve through PaneRenderSpec first, then any available Dart pane package accelerator.',
      interfacePackageRuntime: interfacePackageRuntime,
      issues: List<String>.unmodifiable(diagnostics),
    );
  }

  return InterfacePackageRuntimeReadiness(
    status: InterfacePackageRuntimeReadinessStatus.ready,
    title: 'Interface Package Ready',
    message:
        '${interfacePackageRuntime.interfacePackageName} is available from the static Dart registry. Host-mounted panes resolve through PaneRenderSpec first, then Dart pane-package fallback.',
    interfacePackageRuntime: interfacePackageRuntime,
    issues: List<String>.unmodifiable(diagnostics),
  );
}

InterfacePackageRuntime? _resolveStaticInterfacePackageRuntime({
  required InterfacePackageRuntimeRegistry registry,
  required InterfaceResolvedView? resolvedView,
  required InterfacePackageRuntime? hostPackageRuntime,
}) {
  if (hostPackageRuntime == null) {
    return registry.resolve(
      interfacePackageId: resolvedView?.interfacePackageId?.uuid,
      interfacePackageName: resolvedView?.interfacePackageName,
      experienceKey: resolvedView?.experienceKey,
    );
  }

  final byHostViewIdentity = registry.resolve(
    interfacePackageId: resolvedView?.interfacePackageId?.uuid,
    interfacePackageName: resolvedView?.interfacePackageName,
  );
  if (byHostViewIdentity != null) {
    return byHostViewIdentity;
  }

  final byHostRuntime = registry.resolve(
    interfacePackageId: hostPackageRuntime.interfacePackageId,
    interfacePackageName: hostPackageRuntime.interfacePackageName,
  );
  if (byHostRuntime != null) {
    return byHostRuntime;
  }
  return null;
}

bool _runtimeHasHostBootstrapPaneContributions(InterfaceRuntimeState runtime) {
  if (runtime.windowLayout?.sourceKind ==
      'interface_bootstrap_pane_contributions') {
    return true;
  }
  return runtime.resolvedPanes.any(
    (pane) => pane.stateSourceKind == 'host_pane_contribution',
  );
}

Future<InterfaceHostState> activateInterfaceLayout({
  required InterfaceHostStateNotifier notifier,
  required InterfaceRuntimeLayoutCatalogOption option,
}) {
  return notifier.activateRuntimeLayout(
    layoutConfigId: option.layout.layoutConfigId,
  );
}

Future<InterfaceHostState> activateInterfaceLayoutById({
  required InterfaceHostStateNotifier notifier,
  required InterfaceRuntimeLayoutCatalog catalog,
  required String layoutConfigId,
}) {
  final option = catalog.resolveLayout(layoutConfigId: layoutConfigId);
  if (option == null) {
    throw StateError(
      'The compiled interface package did not expose layout '
      '$layoutConfigId in the active runtime layout catalog.',
    );
  }
  return activateInterfaceLayout(notifier: notifier, option: option);
}

Future<InterfaceHostState> activateInterfaceSectionRepresentation({
  required InterfaceHostStateNotifier notifier,
  required InterfaceRuntimeSectionRepresentationOption option,
}) {
  return notifier.activateRuntimeRepresentation(
    representationId: option.representation.representationId,
  );
}

Future<InterfaceHostState> activateInterfaceSectionRepresentationById({
  required InterfaceHostStateNotifier notifier,
  required InterfaceRuntimeSectionRepresentationCatalog catalog,
  required String representationId,
}) {
  final option = catalog.resolveRepresentation(representationId);
  if (option == null) {
    throw StateError(
      'The compiled interface package did not expose representation '
      '$representationId in the active mounted section catalog.',
    );
  }
  return activateInterfaceSectionRepresentation(
    notifier: notifier,
    option: option,
  );
}

InterfaceRuntimeSectionRepresentationResolution
    resolveInterfaceRuntimeSectionRepresentationResolution({
  required InterfaceHostState? hostState,
  required InterfacePackageRuntime? interfacePackageRuntime,
  String? windowKey,
  String? layoutKey,
  String? sectionKey,
}) {
  final catalog = resolveInterfaceRuntimeSectionRepresentationCatalog(
    hostState: hostState,
    interfacePackageRuntime: interfacePackageRuntime,
    windowKey: windowKey,
    layoutKey: layoutKey,
  );
  return catalog.resolveSection(sectionKey);
}

InterfaceRuntimeSectionRepresentationCatalog
    resolveInterfaceRuntimeSectionRepresentationCatalog({
  required InterfaceHostState? hostState,
  required InterfacePackageRuntime? interfacePackageRuntime,
  String? windowKey,
  String? layoutKey,
}) {
  final hostRepresentations = interfaceHostRuntimeSectionRepresentations(
    hostState,
  );
  if (hostRepresentations.isEmpty) {
    return const InterfaceRuntimeSectionRepresentationCatalog();
  }
  if (interfacePackageRuntime == null) {
    return const InterfaceRuntimeSectionRepresentationCatalog(
      errorMessage:
          'Aware Shell exposed mounted section representations without a compiled interface package runtime.',
    );
  }

  final normalizedWindowKey = _normalizeSelectionValue(windowKey);
  final layoutCatalog = resolveInterfaceRuntimeLayoutCatalog(
    hostState: hostState,
    interfacePackageRuntime: interfacePackageRuntime,
  );
  if (layoutCatalog.hasError) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      errorMessage: layoutCatalog.errorMessage,
      errorDetail: layoutCatalog.errorDetail,
    );
  }
  final resolvedLayoutKey = _normalizeSelectionValue(layoutKey) ??
      _normalizeSelectionValue(layoutCatalog.activeLayoutKey) ??
      _resolveSingleRuntimeLayoutKeyFromSectionRepresentations(
        hostRepresentations,
        windowKey: normalizedWindowKey,
      );
  if (resolvedLayoutKey == null) {
    return const InterfaceRuntimeSectionRepresentationCatalog(
      errorMessage:
          'Aware Shell exposed multiple mounted representation layouts without an active layout selection.',
    );
  }

  final layoutHostRepresentations = hostRepresentations.where((representation) {
    if (normalizedWindowKey != null &&
        _normalizeSelectionValue(representation.windowKey) !=
            normalizedWindowKey) {
      return false;
    }
    return _normalizeSelectionValue(representation.layoutKey) ==
        resolvedLayoutKey;
  }).toList(growable: false);
  if (layoutHostRepresentations.isEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      errorMessage:
          'Aware Shell did not expose mounted section representations for the active layout.',
      errorDetail: resolvedLayoutKey,
    );
  }

  final layoutRepresentations =
      interfacePackageRuntime.resolveSectionRepresentations(
    windowKey: windowKey,
    layoutKey: resolvedLayoutKey,
  );
  if (layoutRepresentations.isEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      errorMessage:
          'The compiled interface package does not declare section representations for the active layout.',
      errorDetail: resolvedLayoutKey,
    );
  }

  final sectionKeys = _resolveMountedSectionKeysFromSectionRepresentations(
    layoutHostRepresentations,
  );
  if (sectionKeys.isEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      errorMessage:
          'Aware Shell emitted no mounted section keys for the active layout.',
      errorDetail: resolvedLayoutKey,
    );
  }

  final resolvedActiveSectionKey =
      _resolveActiveSectionKeyFromSectionRepresentations(
    representations: layoutHostRepresentations,
    activeSectionKey: null,
  );

  final compiledRepresentationCatalog =
      <String, InterfacePackageRuntimeSectionRepresentation>{};
  for (final representation in layoutRepresentations) {
    final representationId = _normalizeSelectionValue(
      representation.representationId,
    );
    if (representationId == null) {
      return InterfaceRuntimeSectionRepresentationCatalog(
        layoutKey: resolvedLayoutKey,
        activeSectionKey: resolvedActiveSectionKey,
        sectionKeys: List<String>.unmodifiable(sectionKeys),
        errorMessage:
            'The compiled interface package emitted a section representation without representation identity.',
      );
    }
    if (compiledRepresentationCatalog.containsKey(representationId)) {
      return InterfaceRuntimeSectionRepresentationCatalog(
        layoutKey: resolvedLayoutKey,
        activeSectionKey: resolvedActiveSectionKey,
        sectionKeys: List<String>.unmodifiable(sectionKeys),
        errorMessage:
            'The compiled interface package emitted duplicate representation identities in the active layout.',
        errorDetail: representationId,
      );
    }
    compiledRepresentationCatalog[representationId] = representation;
  }

  final hostRepresentationCatalog =
      <String, InterfaceRuntimeSectionRepresentationState>{};
  for (final representation in layoutHostRepresentations) {
    final representationId = _normalizeSelectionValue(
      representation.representationId.uuid,
    );
    if (representationId == null) {
      return InterfaceRuntimeSectionRepresentationCatalog(
        layoutKey: resolvedLayoutKey,
        activeSectionKey: resolvedActiveSectionKey,
        sectionKeys: List<String>.unmodifiable(sectionKeys),
        errorMessage:
            'Aware Shell exposed a mounted section representation without representation identity.',
      );
    }
    if (hostRepresentationCatalog.containsKey(representationId)) {
      return InterfaceRuntimeSectionRepresentationCatalog(
        layoutKey: resolvedLayoutKey,
        activeSectionKey: resolvedActiveSectionKey,
        sectionKeys: List<String>.unmodifiable(sectionKeys),
        errorMessage:
            'Aware Shell exposed duplicate mounted section representation identities.',
        errorDetail: representationId,
      );
    }
    hostRepresentationCatalog[representationId] = representation;
  }

  final undeclaredHostRepresentations = hostRepresentationCatalog.keys
      .where(
        (representationId) =>
            !compiledRepresentationCatalog.containsKey(representationId),
      )
      .toList(growable: false);
  if (undeclaredHostRepresentations.isNotEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      activeSectionKey: resolvedActiveSectionKey,
      sectionKeys: List<String>.unmodifiable(sectionKeys),
      errorMessage:
          'Aware Shell exposed mounted section representations that are not declared by the compiled interface package.',
      errorDetail: undeclaredHostRepresentations.join(', '),
    );
  }

  final missingHostRepresentations = compiledRepresentationCatalog.keys
      .where(
        (representationId) =>
            !hostRepresentationCatalog.containsKey(representationId),
      )
      .toList(growable: false);
  if (missingHostRepresentations.isNotEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      activeSectionKey: resolvedActiveSectionKey,
      sectionKeys: List<String>.unmodifiable(sectionKeys),
      errorMessage:
          'Aware Shell did not expose all compiled mounted section representations for the active layout.',
      errorDetail: missingHostRepresentations.join(', '),
    );
  }

  final sectionHostRepresentations =
      <String, List<InterfaceRuntimeSectionRepresentationState>>{};
  for (final representation in layoutHostRepresentations) {
    final sectionKey = _normalizeSelectionValue(representation.sectionKey);
    if (sectionKey == null) {
      return InterfaceRuntimeSectionRepresentationCatalog(
        layoutKey: resolvedLayoutKey,
        activeSectionKey: resolvedActiveSectionKey,
        sectionKeys: List<String>.unmodifiable(sectionKeys),
        errorMessage:
            'Aware Shell exposed a mounted section representation without section identity.',
      );
    }
    sectionHostRepresentations
        .putIfAbsent(
          sectionKey,
          () => <InterfaceRuntimeSectionRepresentationState>[],
        )
        .add(representation);
  }

  final sectionCompiledRepresentations =
      <String, List<InterfacePackageRuntimeSectionRepresentation>>{};
  for (final representation in layoutRepresentations) {
    final sectionKey = _normalizeSelectionValue(representation.sectionKey);
    if (sectionKey == null) {
      return InterfaceRuntimeSectionRepresentationCatalog(
        layoutKey: resolvedLayoutKey,
        activeSectionKey: resolvedActiveSectionKey,
        sectionKeys: List<String>.unmodifiable(sectionKeys),
        errorMessage:
            'The compiled interface package emitted a section representation without section identity.',
      );
    }
    sectionCompiledRepresentations
        .putIfAbsent(
          sectionKey,
          () => <InterfacePackageRuntimeSectionRepresentation>[],
        )
        .add(representation);
  }

  final missingCompiledSections = sectionKeys
      .where(
        (sectionKey) => !sectionCompiledRepresentations.containsKey(sectionKey),
      )
      .toList(growable: false);
  if (missingCompiledSections.isNotEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      activeSectionKey: resolvedActiveSectionKey,
      sectionKeys: List<String>.unmodifiable(sectionKeys),
      errorMessage:
          'The compiled interface package does not declare section representations for mounted host sections.',
      errorDetail: missingCompiledSections.join(', '),
    );
  }

  final missingHostSections = sectionCompiledRepresentations.keys
      .where(
        (sectionKey) => !sectionHostRepresentations.containsKey(sectionKey),
      )
      .toList(growable: false);
  if (missingHostSections.isNotEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      activeSectionKey: resolvedActiveSectionKey,
      sectionKeys: List<String>.unmodifiable(sectionKeys),
      errorMessage:
          'Aware Shell did not mount compiled interface sections for the active layout.',
      errorDetail: missingHostSections.join(', '),
    );
  }

  final sectionKeysWithExtras = sectionHostRepresentations.keys
      .where((sectionKey) => !sectionKeys.contains(sectionKey))
      .toList(growable: false);
  if (sectionKeysWithExtras.isNotEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      activeSectionKey: resolvedActiveSectionKey,
      sectionKeys: List<String>.unmodifiable(sectionKeys),
      errorMessage:
          'Aware Shell exposed mounted section representations outside the active layout section order.',
      errorDetail: sectionKeysWithExtras.join(', '),
    );
  }

  final compiledSectionKeysWithExtras = sectionCompiledRepresentations.keys
      .where((sectionKey) => !sectionKeys.contains(sectionKey))
      .toList(growable: false);
  if (compiledSectionKeysWithExtras.isNotEmpty) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      activeSectionKey: resolvedActiveSectionKey,
      sectionKeys: List<String>.unmodifiable(sectionKeys),
      errorMessage:
          'The compiled interface package declared section representations outside the active mounted section order.',
      errorDetail: compiledSectionKeysWithExtras.join(', '),
    );
  }

  final mountedWindowKeys = layoutHostRepresentations
      .map(
        (representation) => _normalizeSelectionValue(representation.windowKey),
      )
      .whereType<String>()
      .toSet();
  if (mountedWindowKeys.length > 1) {
    return InterfaceRuntimeSectionRepresentationCatalog(
      layoutKey: resolvedLayoutKey,
      activeSectionKey: resolvedActiveSectionKey,
      sectionKeys: List<String>.unmodifiable(sectionKeys),
      errorMessage:
          'Aware Shell exposed mounted section representations for multiple windows in the active layout catalog.',
      errorDetail: mountedWindowKeys.join(', '),
    );
  }

  final resolvedWindowKey = normalizedWindowKey ??
      (mountedWindowKeys.length == 1 ? mountedWindowKeys.first : null);
  if (resolvedWindowKey != null) {
    final compiledWindowKeys = layoutRepresentations
        .map(
          (representation) =>
              _normalizeSelectionValue(representation.windowKey),
        )
        .whereType<String>()
        .toSet();
    if (compiledWindowKeys.length != 1 ||
        !compiledWindowKeys.contains(resolvedWindowKey)) {
      return InterfaceRuntimeSectionRepresentationCatalog(
        layoutKey: resolvedLayoutKey,
        activeSectionKey: resolvedActiveSectionKey,
        sectionKeys: List<String>.unmodifiable(sectionKeys),
        errorMessage:
            'The compiled interface package and Aware Shell disagree on the active mounted window.',
        errorDetail:
            'host=$resolvedWindowKey compiled=${compiledWindowKeys.join(', ')}',
      );
    }
  }

  final sectionKeysByOrder = List<String>.unmodifiable(sectionKeys);
  final resolutions =
      <String, InterfaceRuntimeSectionRepresentationResolution>{};
  for (final resolvedSectionKey in sectionKeysByOrder) {
    resolutions[resolvedSectionKey] =
        _resolveSectionRepresentationResolutionForSection(
      resolvedLayoutKey: resolvedLayoutKey,
      resolvedSectionKey: resolvedSectionKey,
      hostRepresentations: sectionHostRepresentations[resolvedSectionKey] ??
          const <InterfaceRuntimeSectionRepresentationState>[],
      compiledRepresentations:
          sectionCompiledRepresentations[resolvedSectionKey] ??
              const <InterfacePackageRuntimeSectionRepresentation>[],
    );
  }

  return InterfaceRuntimeSectionRepresentationCatalog(
    layoutKey: resolvedLayoutKey,
    activeSectionKey: resolvedActiveSectionKey,
    sectionKeys: sectionKeysByOrder,
    sections: Map<String,
            InterfaceRuntimeSectionRepresentationResolution>.unmodifiable(
        resolutions),
  );
}

InterfaceRuntimeLayoutCatalog resolveInterfaceRuntimeLayoutCatalog({
  required InterfaceHostState? hostState,
  required InterfacePackageRuntime? interfacePackageRuntime,
}) {
  final hostLayoutStates = interfaceHostRuntimeLayoutStates(hostState);
  if (hostLayoutStates.isEmpty) {
    return const InterfaceRuntimeLayoutCatalog();
  }
  if (interfacePackageRuntime == null) {
    return const InterfaceRuntimeLayoutCatalog(
      errorMessage:
          'Aware Shell exposed runtime layouts without a compiled interface package runtime.',
    );
  }

  final compiledLayouts = interfacePackageRuntime.layouts;
  if (compiledLayouts.isEmpty) {
    return const InterfaceRuntimeLayoutCatalog(
      errorMessage:
          'The compiled interface package does not declare runtime layouts for the active selector rail.',
    );
  }

  final compiledLayoutCatalog = <String, InterfacePackageRuntimeLayout>{};
  for (final layout in compiledLayouts) {
    final layoutConfigId = _normalizeSelectionValue(layout.layoutConfigId);
    if (layoutConfigId == null) {
      return const InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'The compiled interface package emitted a runtime layout without layout identity.',
      );
    }
    if (compiledLayoutCatalog.containsKey(layoutConfigId)) {
      return InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'The compiled interface package emitted duplicate runtime layout identities.',
        errorDetail: layoutConfigId,
      );
    }
    compiledLayoutCatalog[layoutConfigId] = layout;
  }

  final hostLayoutCatalog = <String, InterfaceRuntimeLayoutState>{};
  for (final layout in hostLayoutStates) {
    final layoutConfigId = _normalizeSelectionValue(
      layout.layoutConfigId?.uuid,
    );
    if (layoutConfigId == null) {
      return const InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'Aware Shell exposed a mounted runtime layout without layout identity.',
      );
    }
    if (hostLayoutCatalog.containsKey(layoutConfigId)) {
      return InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'Aware Shell exposed duplicate mounted runtime layout identities.',
        errorDetail: layoutConfigId,
      );
    }
    hostLayoutCatalog[layoutConfigId] = layout;
  }

  final undeclaredHostLayouts = hostLayoutCatalog.keys
      .where(
        (layoutConfigId) => !compiledLayoutCatalog.containsKey(layoutConfigId),
      )
      .toList(growable: false);
  if (undeclaredHostLayouts.isNotEmpty) {
    return InterfaceRuntimeLayoutCatalog(
      errorMessage:
          'Aware Shell exposed mounted runtime layouts that are not declared by the compiled interface package.',
      errorDetail: undeclaredHostLayouts.join(', '),
    );
  }

  final missingHostLayouts = compiledLayoutCatalog.keys
      .where((layoutConfigId) => !hostLayoutCatalog.containsKey(layoutConfigId))
      .toList(growable: false);
  if (missingHostLayouts.isNotEmpty) {
    return InterfaceRuntimeLayoutCatalog(
      errorMessage:
          'Aware Shell did not expose all compiled mounted runtime layouts.',
      errorDetail: missingHostLayouts.join(', '),
    );
  }

  final options = <InterfaceRuntimeLayoutCatalogOption>[];
  for (final layout in compiledLayouts) {
    final layoutConfigId = _normalizeSelectionValue(layout.layoutConfigId)!;
    final hostLayout = hostLayoutCatalog[layoutConfigId];
    if (hostLayout == null) {
      return InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'Aware Shell did not expose a compiled mounted runtime layout.',
        errorDetail: layoutConfigId,
      );
    }
    if (_normalizeSelectionValue(layout.layoutKey) !=
        _normalizeSelectionValue(hostLayout.layoutKey)) {
      return InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'The compiled interface package and Aware Shell disagree on mounted runtime layout key.',
        errorDetail:
            '$layoutConfigId: compiled=${layout.layoutKey} host=${hostLayout.layoutKey}',
      );
    }
    if (_normalizeSelectionValue(layout.label) !=
        _normalizeSelectionValue(hostLayout.label)) {
      return InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'The compiled interface package and Aware Shell disagree on mounted runtime layout label.',
        errorDetail:
            '$layoutConfigId: compiled=${layout.label} host=${hostLayout.label}',
      );
    }
    if (layout.isDefault != hostLayout.isDefault) {
      return InterfaceRuntimeLayoutCatalog(
        errorMessage:
            'The compiled interface package and Aware Shell disagree on mounted runtime layout default state.',
        errorDetail:
            '$layoutConfigId: compiled=${layout.isDefault} host=${hostLayout.isDefault}',
      );
    }
    options.add(
      InterfaceRuntimeLayoutCatalogOption(
        layout: layout,
        isActive: hostLayout.isActive,
      ),
    );
  }

  final activeLayoutConfigIds = hostLayoutStates
      .where((layout) => layout.isActive)
      .map((layout) => _normalizeSelectionValue(layout.layoutConfigId?.uuid))
      .whereType<String>()
      .toSet();
  if (activeLayoutConfigIds.length > 1) {
    return InterfaceRuntimeLayoutCatalog(
      errorMessage:
          'Aware Shell exposed multiple active mounted runtime layouts.',
      errorDetail: activeLayoutConfigIds.join(', '),
    );
  }
  final activeLayoutConfigId = activeLayoutConfigIds.isEmpty
      ? _normalizeSelectionValue(hostState?.runtime?.activeLayoutConfigId?.uuid)
      : activeLayoutConfigIds.single;
  String? resolvedActiveLayoutConfigId = activeLayoutConfigId;
  if (resolvedActiveLayoutConfigId == null && options.length == 1) {
    resolvedActiveLayoutConfigId = _normalizeSelectionValue(
      options.single.layout.layoutConfigId,
    );
  }
  if (resolvedActiveLayoutConfigId == null) {
    return const InterfaceRuntimeLayoutCatalog(
      errorMessage:
          'Aware Shell exposed multiple runtime layouts without an active compiled layout selection.',
    );
  }

  final resolvedOptions = options.map((option) {
    final layoutConfigId = _normalizeSelectionValue(
      option.layout.layoutConfigId,
    );
    final isActive = layoutConfigId == resolvedActiveLayoutConfigId;
    if (option.isActive == isActive) {
      return option;
    }
    return InterfaceRuntimeLayoutCatalogOption(
      layout: option.layout,
      isActive: isActive,
    );
  }).toList(growable: false);
  final activeOption = resolvedOptions
      .where((option) => option.isActive)
      .toList(growable: false);
  if (activeOption.length != 1) {
    return InterfaceRuntimeLayoutCatalog(
      errorMessage:
          'The compiled interface package and Aware Shell disagree on the active runtime layout selection.',
      errorDetail: resolvedActiveLayoutConfigId,
    );
  }

  return InterfaceRuntimeLayoutCatalog(
    options: List<InterfaceRuntimeLayoutCatalogOption>.unmodifiable(
      resolvedOptions,
    ),
    activeLayoutConfigId: resolvedActiveLayoutConfigId,
    activeLayoutKey: activeOption.single.layout.layoutKey,
  );
}

InterfaceRuntimeSectionRepresentationResolution
    _resolveSectionRepresentationResolutionForSection({
  required String resolvedLayoutKey,
  required String resolvedSectionKey,
  required List<InterfaceRuntimeSectionRepresentationState> hostRepresentations,
  required List<InterfacePackageRuntimeSectionRepresentation>
      compiledRepresentations,
}) {
  if (compiledRepresentations.isEmpty) {
    return InterfaceRuntimeSectionRepresentationResolution(
      layoutKey: resolvedLayoutKey,
      sectionKey: resolvedSectionKey,
      errorMessage:
          'The compiled interface package is missing section representations for the active selector rail.',
      errorDetail: '$resolvedLayoutKey.$resolvedSectionKey',
    );
  }
  if (hostRepresentations.isEmpty) {
    return InterfaceRuntimeSectionRepresentationResolution(
      layoutKey: resolvedLayoutKey,
      sectionKey: resolvedSectionKey,
      errorMessage:
          'Aware Shell did not expose mounted section representations for the requested section.',
      errorDetail: '$resolvedLayoutKey.$resolvedSectionKey',
    );
  }

  final compiledRepresentationCatalog =
      <String, InterfacePackageRuntimeSectionRepresentation>{};
  for (final representation in compiledRepresentations) {
    final representationId = _normalizeSelectionValue(
      representation.representationId,
    );
    if (representationId == null) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package emitted a section representation without representation identity.',
      );
    }
    if (compiledRepresentationCatalog.containsKey(representationId)) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package emitted duplicate representation identities in one mounted section.',
        errorDetail: representationId,
      );
    }
    compiledRepresentationCatalog[representationId] = representation;
  }

  final options = <InterfaceRuntimeSectionRepresentationOption>[];
  for (final hostRepresentation in hostRepresentations) {
    final representationId = _normalizeSelectionValue(
      hostRepresentation.representationId.uuid,
    );
    if (representationId == null) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'Aware Shell exposed a mounted section representation without representation identity.',
      );
    }
    final representation = compiledRepresentationCatalog.remove(
      representationId,
    );
    if (representation == null) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell mounted representation catalog drifted.',
        errorDetail: representationId,
      );
    }
    if (_normalizeSelectionValue(hostRepresentation.sectionKey) !=
        _normalizeSelectionValue(representation.sectionKey)) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell disagree on mounted section identity.',
        errorDetail:
            '$representationId: compiled=${representation.sectionKey} host=${hostRepresentation.sectionKey}',
      );
    }
    if (_normalizeSelectionValue(hostRepresentation.layoutKey) !=
        _normalizeSelectionValue(representation.layoutKey)) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell disagree on mounted layout identity.',
        errorDetail:
            '$representationId: compiled=${representation.layoutKey} host=${hostRepresentation.layoutKey}',
      );
    }
    final hostObservableId = hostRepresentation.observableId.uuid;
    if (hostObservableId != representation.observableId) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell disagree on the active observable contract.',
        errorDetail:
            '$representationId: compiled=${representation.observableId} host=$hostObservableId',
      );
    }
    if (_normalizeSelectionValue(hostRepresentation.viewRef) !=
        _normalizeSelectionValue(representation.viewRef)) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell disagree on the experience view binding.',
        errorDetail:
            '$representationId: compiled=${representation.viewRef} host=${hostRepresentation.viewRef}',
      );
    }
    if (_normalizeSelectionValue(hostRepresentation.projectionViewKey) !=
        _normalizeSelectionValue(representation.projectionViewKey)) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell disagree on projection view identity.',
        errorDetail:
            '$representationId: compiled=${representation.projectionViewKey} host=${hostRepresentation.projectionViewKey}',
      );
    }
    if (_normalizeSelectionValue(hostRepresentation.paneName) !=
        _normalizeSelectionValue(representation.paneName)) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell disagree on pane-name identity.',
        errorDetail:
            '$representationId: compiled=${representation.paneName} host=${hostRepresentation.paneName}',
      );
    }
    if (_normalizeSelectionValue(hostRepresentation.paneKind) !=
        _normalizeSelectionValue(representation.paneKind)) {
      return InterfaceRuntimeSectionRepresentationResolution(
        layoutKey: resolvedLayoutKey,
        sectionKey: resolvedSectionKey,
        errorMessage:
            'The compiled interface package and Aware Shell disagree on pane-kind identity.',
        errorDetail:
            '$representationId: compiled=${representation.paneKind} host=${hostRepresentation.paneKind}',
      );
    }
    options.add(
      InterfaceRuntimeSectionRepresentationOption(
        representation: representation,
        isActive: hostRepresentation.isActive,
      ),
    );
  }
  if (compiledRepresentationCatalog.isNotEmpty) {
    return InterfaceRuntimeSectionRepresentationResolution(
      layoutKey: resolvedLayoutKey,
      sectionKey: resolvedSectionKey,
      errorMessage:
          'Aware Shell did not expose all compiled representations for the mounted section.',
      errorDetail: compiledRepresentationCatalog.keys.join(', '),
    );
  }

  return InterfaceRuntimeSectionRepresentationResolution(
    options: List<InterfaceRuntimeSectionRepresentationOption>.unmodifiable(
      options,
    ),
    layoutKey: resolvedLayoutKey,
    sectionKey: resolvedSectionKey,
  );
}

List<String> _interfacePackageIdentityIssues({
  required InterfaceResolvedView resolvedView,
  required InterfacePackageRuntime interfacePackageRuntime,
}) {
  final issues = <String>[];
  final hostPackageId = _normalizeSelectionValue(
    resolvedView.interfacePackageId?.uuid,
  );
  final runtimePackageId = _normalizeSelectionValue(
    interfacePackageRuntime.interfacePackageId,
  );
  if (hostPackageId != null && hostPackageId != runtimePackageId) {
    issues.add(
      'interface_package_id_mismatch:host=$hostPackageId runtime=$runtimePackageId',
    );
  }

  final hostPackageName = _normalizeSelectionValue(
    resolvedView.interfacePackageName,
  );
  final runtimePackageName = _normalizeSelectionValue(
    interfacePackageRuntime.interfacePackageName,
  );
  if (hostPackageName != null && hostPackageName != runtimePackageName) {
    issues.add(
      'interface_package_name_mismatch:host=$hostPackageName runtime=$runtimePackageName',
    );
  }
  return issues;
}

List<String> _interfaceRuntimeLayoutIssues({
  required InterfaceRuntimeState runtime,
  required InterfacePackageRuntime interfacePackageRuntime,
}) {
  final issues = <String>[];
  final compiledById = <String, InterfacePackageRuntimeLayout>{};
  final compiledByKey = <String, InterfacePackageRuntimeLayout>{};
  for (final layout in interfacePackageRuntime.layouts) {
    final layoutId = _normalizeSelectionValue(layout.layoutConfigId);
    final layoutKey = _normalizeSelectionValue(layout.layoutKey);
    if (layoutId != null) {
      compiledById[layoutId] = layout;
    }
    if (layoutKey != null) {
      compiledByKey[layoutKey] = layout;
    }
  }

  for (final hostLayout in runtime.layoutStates) {
    final layoutId = _normalizeSelectionValue(hostLayout.layoutConfigId?.uuid);
    final layoutKey = _normalizeSelectionValue(hostLayout.layoutKey);
    final compiledLayout = (layoutId == null ? null : compiledById[layoutId]) ??
        (layoutKey == null ? null : compiledByKey[layoutKey]);
    if (compiledLayout == null) {
      issues.add(
        'undeclared_runtime_layout:${layoutId ?? layoutKey ?? '<unknown>'}',
      );
      continue;
    }
    final compiledLayoutKey = _normalizeSelectionValue(
      compiledLayout.layoutKey,
    );
    if (layoutKey != null && layoutKey != compiledLayoutKey) {
      issues.add(
        'runtime_layout_key_mismatch:${layoutId ?? layoutKey}:host=$layoutKey compiled=$compiledLayoutKey',
      );
    }
  }

  final windowLayout = interfaceHostRuntimeWindowLayoutPayload(
    InterfaceHostState(
      hostLabel: '',
      namespace: '',
      started: true,
      transport: InterfaceTransportState(
        available: false,
        registered: false,
        authenticated: false,
      ),
      runtime: runtime,
    ),
  );
  final windowLayoutId = _normalizeSelectionValue(
    _stringValue(windowLayout?['layout_config_id']),
  );
  final windowLayoutKey = _normalizeSelectionValue(
    _stringValue(windowLayout?['layout_key']),
  );
  if (windowLayoutId != null && !compiledById.containsKey(windowLayoutId)) {
    issues.add('undeclared_window_layout:$windowLayoutId');
  } else if (windowLayoutId == null &&
      windowLayoutKey != null &&
      !compiledByKey.containsKey(windowLayoutKey)) {
    issues.add('undeclared_window_layout:$windowLayoutKey');
  }

  return issues;
}

List<String> _interfaceRuntimeSectionRepresentationIssues({
  required InterfaceRuntimeState runtime,
  required InterfacePackageRuntime interfacePackageRuntime,
}) {
  final compiledById = <String, InterfacePackageRuntimeSectionRepresentation>{};
  for (final representation in interfacePackageRuntime.sectionRepresentations) {
    final representationId = _normalizeSelectionValue(
      representation.representationId,
    );
    if (representationId != null) {
      compiledById[representationId] = representation;
    }
  }

  final issues = <String>[];
  for (final hostRepresentation in runtime.sectionRepresentations) {
    final representationId = _normalizeSelectionValue(
      hostRepresentation.representationId.uuid,
    );
    if (representationId == null) {
      issues.add('mounted_section_representation_missing_id');
      continue;
    }
    final compiledRepresentation = compiledById[representationId];
    if (compiledRepresentation == null) {
      issues.add('undeclared_section_representation:$representationId');
      continue;
    }
    issues.addAll(
      _sectionRepresentationFieldIssues(
        representationId: representationId,
        hostRepresentation: hostRepresentation,
        compiledRepresentation: compiledRepresentation,
      ),
    );
  }
  return issues;
}

List<String> _sectionRepresentationFieldIssues({
  required String representationId,
  required InterfaceRuntimeSectionRepresentationState hostRepresentation,
  required InterfacePackageRuntimeSectionRepresentation compiledRepresentation,
}) {
  final issues = <String>[];
  void compare(String field, String? hostValue, String? compiledValue) {
    final normalizedHost = _normalizeSelectionValue(hostValue);
    final normalizedCompiled = _normalizeSelectionValue(compiledValue);
    if (normalizedHost != normalizedCompiled) {
      issues.add(
        'section_representation_${field}_mismatch:$representationId:host=$normalizedHost compiled=$normalizedCompiled',
      );
    }
  }

  compare(
    'window_key',
    hostRepresentation.windowKey,
    compiledRepresentation.windowKey,
  );
  compare(
    'layout_key',
    hostRepresentation.layoutKey,
    compiledRepresentation.layoutKey,
  );
  compare(
    'section_key',
    hostRepresentation.sectionKey,
    compiledRepresentation.sectionKey,
  );
  compare(
    'pane_name',
    hostRepresentation.paneName,
    compiledRepresentation.paneName,
  );
  compare(
    'pane_kind',
    hostRepresentation.paneKind,
    compiledRepresentation.paneKind,
  );
  compare('label', hostRepresentation.label, compiledRepresentation.label);
  compare(
    'observable_id',
    hostRepresentation.observableId.uuid,
    compiledRepresentation.observableId,
  );
  compare(
    'view_ref',
    hostRepresentation.viewRef,
    compiledRepresentation.viewRef,
  );
  compare(
    'projection_view_key',
    hostRepresentation.projectionViewKey,
    compiledRepresentation.projectionViewKey,
  );
  return issues;
}

List<String> _interfaceRuntimePanePackageIssues({
  required InterfaceRuntimeState runtime,
  required InterfacePackageRuntime interfacePackageRuntime,
}) {
  final issues = <String>[];
  final seen = <String>{};
  for (final pane in runtime.resolvedPanes) {
    final panePackageId = pane.panePackageId;
    if (panePackageId == null) {
      issues.add('resolved_pane_missing_package_id:${pane.paneKind}');
      continue;
    }
    final key = panePackageId.uuid;
    if (!seen.add(key)) {
      continue;
    }
    final registration = interfacePackageRuntime.panePackageRegistry
        .registrationFor(panePackageId);
    if (registration == null) {
      issues.add('unregistered_pane_package:$key');
      continue;
    }
    final hostPaneName = _normalizeSelectionValue(pane.panePackageName);
    final compiledPaneName = _normalizeSelectionValue(
      registration.panePackageName,
    );
    if (hostPaneName != null &&
        compiledPaneName != null &&
        hostPaneName != compiledPaneName) {
      issues.add(
        'pane_package_name_mismatch:$key:host=$hostPaneName compiled=$compiledPaneName',
      );
    }
    final hostPaneKind = _normalizeSelectionValue(pane.paneKind);
    final compiledPaneKind = _normalizeSelectionValue(registration.paneKind);
    if (hostPaneKind != null && hostPaneKind != compiledPaneKind) {
      issues.add(
        'pane_package_kind_mismatch:$key:host=$hostPaneKind compiled=$compiledPaneKind',
      );
    }
  }
  return issues;
}

String _hostInterfacePackageLabel(InterfaceResolvedView resolvedView) {
  final packageName = _normalizeSelectionValue(
    resolvedView.interfacePackageName,
  );
  if (packageName != null) {
    return packageName;
  }
  final packageId = _normalizeSelectionValue(
    resolvedView.interfacePackageId?.uuid,
  );
  if (packageId != null) {
    return packageId;
  }
  final experienceKey = _normalizeSelectionValue(resolvedView.experienceKey);
  if (experienceKey != null) {
    return experienceKey;
  }
  return '<unknown>';
}

String? _stringValue(Object? value) {
  if (value is! String) {
    return null;
  }
  final trimmed = value.trim();
  return trimmed.isEmpty ? null : trimmed;
}

Set<String> _resolveSwitchableSectionsFromSectionRepresentations(
  List<InterfaceRuntimeSectionRepresentationState> representations,
) {
  final counts = <String, int>{};
  for (final representation in representations) {
    final sectionKey = _normalizeSelectionValue(representation.sectionKey);
    if (sectionKey == null) {
      continue;
    }
    counts.update(sectionKey, (value) => value + 1, ifAbsent: () => 1);
  }
  return counts.entries
      .where((entry) => entry.value > 1)
      .map((entry) => entry.key)
      .toSet();
}

List<String> _resolveMountedSectionKeysFromSectionRepresentations(
  List<InterfaceRuntimeSectionRepresentationState> representations,
) {
  final sectionKeys = <String>[];
  final seenSectionKeys = <String>{};
  for (final representation in representations) {
    final sectionKey = _normalizeSelectionValue(representation.sectionKey);
    if (sectionKey == null || seenSectionKeys.contains(sectionKey)) {
      continue;
    }
    seenSectionKeys.add(sectionKey);
    sectionKeys.add(sectionKey);
  }
  return sectionKeys;
}

String? _resolveActiveSectionKeyFromSectionRepresentations({
  required List<InterfaceRuntimeSectionRepresentationState> representations,
  required String? activeSectionKey,
}) {
  final activeSections = representations
      .where((representation) => representation.isActive)
      .map(
        (representation) => _normalizeSelectionValue(representation.sectionKey),
      )
      .whereType<String>()
      .toSet();
  if (activeSections.length == 1) {
    return activeSections.first;
  }
  final switchableSections =
      _resolveSwitchableSectionsFromSectionRepresentations(representations);
  if (activeSectionKey != null &&
      switchableSections.contains(activeSectionKey)) {
    return activeSectionKey;
  }
  if (switchableSections.length == 1) {
    return switchableSections.first;
  }
  final sectionKeys = representations
      .map(
        (representation) => _normalizeSelectionValue(representation.sectionKey),
      )
      .whereType<String>()
      .toSet();
  if (sectionKeys.length == 1) {
    return sectionKeys.first;
  }
  return null;
}

String? _resolveSingleRuntimeLayoutKeyFromSectionRepresentations(
  List<InterfaceRuntimeSectionRepresentationState> representations, {
  String? windowKey,
}) {
  final normalizedWindowKey = _normalizeSelectionValue(windowKey);
  final layoutKeys = representations
      .where((representation) {
        if (normalizedWindowKey == null) {
          return true;
        }
        return _normalizeSelectionValue(representation.windowKey) ==
            normalizedWindowKey;
      })
      .map(
        (representation) => _normalizeSelectionValue(representation.layoutKey),
      )
      .whereType<String>()
      .toSet();
  if (layoutKeys.length != 1) {
    return null;
  }
  return layoutKeys.first;
}

String? _normalizeSelectionValue(String? value) {
  final normalized = value?.trim().toLowerCase();
  if (normalized == null || normalized.isEmpty) {
    return null;
  }
  return normalized;
}

bool _paneRepresentationMatchesKey(
  InterfacePackageRuntimeSectionRepresentation representation,
  String normalizedPaneKey,
) {
  return _normalizeSelectionValue(representation.paneName) ==
          normalizedPaneKey ||
      _normalizeSelectionValue(representation.paneKind) == normalizedPaneKey;
}
