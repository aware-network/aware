import 'package:aware_pane_runtime/aware_pane_runtime.dart' as pane_runtime;
import 'package:aware_shell/aware_shell.dart' as shell;
import 'package:aware_windows/aware_windows.dart';
import 'package:uuid/uuid_value.dart';

import 'aware_app_manifest.dart';

class AwareInterfaceRuntimeAdapter {
  const AwareInterfaceRuntimeAdapter();

  shell.InterfacePackageRuntimeLayout resolveLayout(
    shell.InterfacePackageRuntime runtime, {
    String? layoutKey,
  }) {
    if (runtime.layouts.isEmpty) {
      throw StateError(
        'Interface package `${runtime.interfacePackageName}` declares no layouts.',
      );
    }

    final requestedLayoutKey = layoutKey?.trim();
    if (requestedLayoutKey != null && requestedLayoutKey.isNotEmpty) {
      for (final layout in runtime.layouts) {
        if (layout.layoutKey == requestedLayoutKey) {
          return layout;
        }
      }
    }

    for (final layout in runtime.layouts) {
      if (layout.isDefault) {
        return layout;
      }
    }
    return runtime.layouts.first;
  }

  List<shell.InterfaceShellSection> sectionsForLayout(
    shell.InterfacePackageRuntime runtime, {
    required String layoutKey,
    AwareAppSectionPolicy policy = const AwareAppSectionPolicy.empty(),
  }) {
    final policySections = policy.specsForLayout(layoutKey);
    if (policySections != null && policySections.isNotEmpty) {
      return policySections
          .map((spec) => spec.toShellSection())
          .toList(growable: false);
    }

    final sectionKeys = <String>[];
    for (final representation in runtime.sectionRepresentations) {
      if (representation.layoutKey != layoutKey) {
        continue;
      }
      if (!sectionKeys.contains(representation.sectionKey)) {
        sectionKeys.add(representation.sectionKey);
      }
    }
    if (sectionKeys.isEmpty) {
      return const <shell.InterfaceShellSection>[
        shell.InterfaceShellSection(
          sectionKey: 'workspace',
          region: WindowFullscreenSectionRegion.stage,
          order: 0,
          title: 'Workspace',
        ),
      ];
    }

    return <shell.InterfaceShellSection>[
      for (var index = 0; index < sectionKeys.length; index++)
        shell.InterfaceShellSection(
          sectionKey: sectionKeys[index],
          region: _defaultRegionForIndex(index),
          order: index,
          title: _titleFromSectionKey(sectionKeys[index]),
        ),
    ];
  }

  List<shell.InterfaceResolvedPaneDescriptor> resolvedPanesForLayout(
    shell.InterfacePackageRuntime runtime, {
    required String windowKey,
    required String layoutKey,
  }) {
    return runtime.sectionRepresentations
        .where(
          (representation) =>
              representation.windowKey == windowKey &&
              representation.layoutKey == layoutKey,
        )
        .map(
          (representation) => _descriptorForRepresentation(
            runtime: runtime,
            representation: representation,
          ),
        )
        .toList(growable: false);
  }

  shell.InterfaceResolvedPaneDescriptor _descriptorForRepresentation({
    required shell.InterfacePackageRuntime runtime,
    required shell.InterfacePackageRuntimeSectionRepresentation representation,
  }) {
    final panePackage = _panePackageForRepresentation(
      runtime.panePackageRegistry,
      representation,
    );

    return shell.InterfaceResolvedPaneDescriptor(
      windowKey: representation.windowKey,
      layoutKey: representation.layoutKey,
      sectionKey: representation.sectionKey,
      paneKind: representation.paneKind,
      panePackageId: panePackage?.panePackageId,
      panePackageName: panePackage?.panePackageName,
      objectProjectionGraphObservableId: _uuidOrNull(
        representation.observableId,
      ),
      projectionViewId:
          _trimmedOrNull(representation.projectionViewKey) ??
          _trimmedOrNull(representation.viewRef),
      viewRef: _trimmedOrNull(representation.viewRef),
      projectionViewKey: _trimmedOrNull(representation.projectionViewKey),
      title:
          _trimmedOrNull(representation.label) ??
          _titleFromSectionKey(representation.paneName),
      stateSourceKind: 'interface_package_runtime',
    );
  }

  pane_runtime.PanePackageRegistration? _panePackageForRepresentation(
    pane_runtime.PanePackageRegistry registry,
    shell.InterfacePackageRuntimeSectionRepresentation representation,
  ) {
    for (final panePackageId in registry.registeredPanePackageIds()) {
      final registration = registry.registrationFor(panePackageId);
      if (registration == null) {
        continue;
      }
      if (_sameText(registration.paneKind, representation.paneKind) ||
          _sameText(registration.panePackageName, representation.paneName)) {
        return registration;
      }
    }
    return null;
  }
}

WindowFullscreenSectionRegion _defaultRegionForIndex(int index) {
  return switch (index) {
    0 => WindowFullscreenSectionRegion.stage,
    1 => WindowFullscreenSectionRegion.leading,
    2 => WindowFullscreenSectionRegion.trailing,
    _ => WindowFullscreenSectionRegion.dock,
  };
}

String _titleFromSectionKey(String value) {
  final words = value
      .split(RegExp(r'[_\-\s]+'))
      .where((word) => word.trim().isNotEmpty)
      .map((word) {
        final lower = word.toLowerCase();
        return lower.substring(0, 1).toUpperCase() + lower.substring(1);
      });
  final title = words.join(' ');
  return title.isEmpty ? value : title;
}

UuidValue? _uuidOrNull(String value) {
  final text = _trimmedOrNull(value);
  if (text == null) {
    return null;
  }
  try {
    return UuidValue.fromString(text);
  } on FormatException {
    return null;
  }
}

String? _trimmedOrNull(String? value) {
  final text = value?.trim();
  if (text == null || text.isEmpty) {
    return null;
  }
  return text;
}

bool _sameText(String? left, String? right) {
  final normalizedLeft = _trimmedOrNull(left)?.toLowerCase();
  final normalizedRight = _trimmedOrNull(right)?.toLowerCase();
  return normalizedLeft != null &&
      normalizedRight != null &&
      normalizedLeft == normalizedRight;
}
