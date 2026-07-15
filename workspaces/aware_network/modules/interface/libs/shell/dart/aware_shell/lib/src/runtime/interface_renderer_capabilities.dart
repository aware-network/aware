import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:uuid/uuid.dart';

import 'interface_package_runtime.dart';

const String kInterfaceRendererKindFlutter = 'flutter';
const String kInterfaceRendererCacheStoreMemory = 'memory';

InterfaceRendererCapabilitiesState buildInterfaceRendererCapabilities({
  required InterfacePackageRuntime runtime,
  required String rendererId,
  String rendererKind = kInterfaceRendererKindFlutter,
  String? rendererVersion,
  DateTime? reportedAt,
  InterfaceRendererCacheCapabilityState? cache,
}) {
  return InterfaceRendererCapabilitiesState(
    rendererId: rendererId,
    rendererKind: rendererKind,
    rendererVersion: rendererVersion,
    interfacePackageId: _uuidValueOrNull(runtime.interfacePackageId),
    interfacePackageName: _trimmedOrNull(runtime.interfacePackageName),
    experienceKeys: _nonEmptyStrings(runtime.experienceKeys),
    panePackages: _panePackageCapabilities(runtime),
    viewCapabilities: _viewCapabilities(runtime),
    cache: cache ?? buildMemoryInterfaceRendererCacheCapability(),
    reportedAt: (reportedAt ?? DateTime.now().toUtc()).toIso8601String(),
  );
}

InterfaceRendererCacheCapabilityState
buildMemoryInterfaceRendererCacheCapability() {
  return InterfaceRendererCacheCapabilityState(
    storeKind: kInterfaceRendererCacheStoreMemory,
    supportsNamespaceReplace: true,
    supportsPersistentStorage: false,
    supportsCursorLookup: true,
  );
}

List<InterfaceRendererPanePackageCapabilityState> _panePackageCapabilities(
  InterfacePackageRuntime runtime,
) {
  final capabilities = <InterfaceRendererPanePackageCapabilityState>[];
  for (final panePackageId
      in runtime.panePackageRegistry.registeredPanePackageIds()) {
    final registration = runtime.panePackageRegistry.registrationFor(
      panePackageId,
    );
    if (registration == null) {
      continue;
    }
    capabilities.add(
      InterfaceRendererPanePackageCapabilityState(
        panePackageId: registration.panePackageId,
        panePackageName: _trimmedOrNull(registration.panePackageName),
        paneKind: registration.paneKind,
      ),
    );
  }
  return List<InterfaceRendererPanePackageCapabilityState>.unmodifiable(
    capabilities,
  );
}

List<InterfaceRendererViewCapabilityState> _viewCapabilities(
  InterfacePackageRuntime runtime,
) {
  final capabilities = <InterfaceRendererViewCapabilityState>[];
  final seen = <String>{};
  for (final representation in runtime.sectionRepresentations) {
    final viewRef = _trimmedOrNull(representation.viewRef);
    final projectionViewKey = _trimmedOrNull(representation.projectionViewKey);
    final paneKind = _trimmedOrNull(representation.paneKind);
    final key = '${viewRef ?? ''}|${projectionViewKey ?? ''}|${paneKind ?? ''}';
    if (!seen.add(key)) {
      continue;
    }
    capabilities.add(
      InterfaceRendererViewCapabilityState(
        viewRef: viewRef,
        projectionViewKey: projectionViewKey,
        paneKind: paneKind,
        hasDecoder: runtime.viewStateDecoderRegistry.hasDecoder(
          viewRef: viewRef,
          viewKey: projectionViewKey,
        ),
      ),
    );
  }
  return List<InterfaceRendererViewCapabilityState>.unmodifiable(capabilities);
}

List<String> _nonEmptyStrings(Iterable<String> values) {
  return List<String>.unmodifiable(
    values.map(_trimmedOrNull).whereType<String>(),
  );
}

UuidValue? _uuidValueOrNull(String? value) {
  final normalized = _trimmedOrNull(value);
  if (normalized == null) {
    return null;
  }
  try {
    return UuidValue.fromString(normalized);
  } on FormatException {
    return null;
  }
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
