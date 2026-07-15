import 'package:aware_environment_service_api/aware_environment_service_api.dart';
import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_interface_sdk/aware_interface_sdk.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../runtime/interface_package_runtime.dart';
import '../providers/host_state_provider.dart';
import 'environment_navigator_rail.dart';
import 'shell_section.dart';
import '../providers/pane_api_scope.dart';
import '../render_spec/pane_render_spec.dart';
import '../render_spec/render_component_registry.dart';
import 'runtime_shell.dart';
import 'shell_resolved_pane.dart';

const String _environmentNavigatorApiViewRef = 'environment.navigator';
const String _environmentNavigatorProjectionViewKey =
    'environment.navigator.v1';
const String _threadLayoutApiViewRef = 'environment.thread_layout';
const String _threadLayoutProjectionViewKey = 'thread.layout.v1';

class InterfaceHostRuntimeShell extends StatelessWidget {
  const InterfaceHostRuntimeShell({
    required this.hostState,
    required this.panePackageRegistry,
    super.key,
    this.interfacePackageRuntime,
    this.rendererId,
    this.rendererVersion,
    this.mediaResolver,
    this.header,
    this.onBuild,
    this.clientIntentIdFactory,
    this.onLayoutTransitionCommit,
    this.onLayoutTopologyCommit,
  });

  final InterfaceHostState hostState;
  final PanePackageRegistry panePackageRegistry;
  final InterfacePackageRuntime? interfacePackageRuntime;
  final String? rendererId;
  final String? rendererVersion;
  final InterfaceStorageMediaResolver? mediaResolver;
  final Widget? header;
  final ValueChanged<String>? onBuild;
  final String Function()? clientIntentIdFactory;
  final WindowLayoutTransitionCommitCallback? onLayoutTransitionCommit;
  final WindowLayoutTopologyCommitCallback? onLayoutTopologyCommit;

  @override
  Widget build(BuildContext context) {
    onBuild?.call('InterfaceHostRuntimeShell');
    final runtime = hostState.runtime;
    final windowLayout = _HostWindowLayout.fromHostStateOrNull(hostState);
    if (runtime == null || windowLayout == null) {
      return _InterfaceHostRuntimeShellUnavailable(
        message:
            'Interface Host has not resolved a runtime shell layout for this namespace yet.',
      );
    }
    final dynamicRenderSpecs = paneRenderSpecsFromInterfaceRuntimeState(
      runtime,
    );
    final effectivePackageRuntime =
        interfacePackageRuntime?.withRenderSpecOverlay(dynamicRenderSpecs);
    final environmentNavigator = _environmentNavigatorViewState(runtime);
    final environmentNavigationContextId =
        hostState.environmentNavigation?.environmentNavigationContextId?.uuid;
    final threadLayout = _threadLayoutViewState(runtime);
    final effectiveWindowLayout = _HostWindowLayout.fromThreadLayoutOrNull(
          threadLayout,
          fallback: windowLayout,
        ) ??
        windowLayout;
    final threadLayoutShellPanes = _shellPanesFromThreadLayout(
      threadLayout: threadLayout,
      windowLayout: effectiveWindowLayout,
    );
    final leadingRail = environmentNavigator == null
        ? null
        : EnvironmentNavigatorRail(
            viewState: environmentNavigator,
            environmentNavigationContextId: environmentNavigationContextId,
            onTargetSelected: (selection) {
              final container = ProviderScope.containerOf(
                context,
                listen: false,
              );
              container
                  .read(interfaceHostStateProvider.notifier)
                  .selectEnvironmentNavigationTarget(
                environmentNavigationContextId: _uuidValueOrNull(
                  selection.environmentNavigationContextId,
                ),
                selectedProcessId: _uuidValueOrNull(selection.processId),
                selectedThreadId: _uuidValueOrNull(selection.threadId),
                reason: 'interface_shell_environment_navigator',
                evidence: const <String, dynamic>{
                  'source': 'interface_shell_environment_navigator_rail',
                },
              );
            },
          );
    final renderSpecActionInvoker = (PaneRenderActionInvocation invocation) {
      final container = ProviderScope.containerOf(context, listen: false);
      return container
          .read(interfacePaneActionDispatcherProvider)
          .invokeRenderSpecAction(invocation);
    };
    final effectiveLayoutTransitionCommit = onLayoutTransitionCommit ??
        (WindowLayoutTransitionCommitIntent intent) async {
          final container = ProviderScope.containerOf(context, listen: false);
          await container
              .read(interfaceHostStateProvider.notifier)
              .applyAttentionLayoutTransition(
                clientIntentId: intent.clientIntentId,
                expectedPreviousLayoutTransitionId:
                    intent.expectedPreviousTransitionId == null
                        ? null
                        : UuidValue.fromString(
                            intent.expectedPreviousTransitionId!,
                          ),
                topologyTransitionId: intent.topologyTransitionId == null
                    ? null
                    : UuidValue.fromString(intent.topologyTransitionId!),
                sectionStates: intent.sectionStates
                    .map(
                      (section) =>
                          InterfaceAttentionLayoutTransitionSectionIntent(
                        layoutConfigSectionConfigId: UuidValue.fromString(
                          section.sectionId,
                        ),
                        order: section.order,
                        weightMicros: section.weightMicros,
                        isVisible: section.isVisible,
                        isCollapsed: section.isCollapsed,
                      ),
                    )
                    .toList(growable: false),
              );
        };
    final effectiveLayoutTopologyCommit = onLayoutTopologyCommit ??
        (WindowLayoutTopologyCommitIntent intent) async {
          final container = ProviderScope.containerOf(context, listen: false);
          await container
              .read(interfaceHostStateProvider.notifier)
              .applyAttentionLayoutTopologyTransition(
                clientIntentId: intent.clientIntentId,
                expectedPreviousTopologyTransitionId:
                    intent.expectedPreviousTopologyTransitionId == null
                        ? null
                        : UuidValue.fromString(
                            intent.expectedPreviousTopologyTransitionId!,
                          ),
                sectionStates: intent.sectionStates
                    .map(
                      (section) =>
                          InterfaceAttentionLayoutTopologyTransitionSectionIntent(
                        layoutConfigSectionConfigId: UuidValue.fromString(
                          section.sectionId,
                        ),
                        order: section.order,
                      ),
                    )
                    .toList(growable: false),
              );
        };
    final effectiveClientIntentIdFactory =
        clientIntentIdFactory ?? () => const Uuid().v4();
    final runtimeShell = threadLayoutShellPanes == null
        ? InterfaceRuntimeShell(
            windowKey: effectiveWindowLayout.windowKey,
            layoutKey: effectiveWindowLayout.layoutKey,
            mode: effectiveWindowLayout.mode,
            sections: effectiveWindowLayout.sections,
            admittedSections: effectiveWindowLayout.admittedSections,
            resolvedPanes: runtime.resolvedPanes,
            materializedPaneStates: runtime.materializedPaneStates,
            allowedActions: hostState.allowedActions,
            panePackageRegistry: panePackageRegistry,
            renderSpecs:
                effectivePackageRuntime?.renderSpecs ?? dynamicRenderSpecs,
            renderComponentRegistry:
                effectivePackageRuntime?.renderComponentRegistry ??
                    const RenderComponentRegistry.empty(),
            mediaResolver: mediaResolver,
            leadingRail: leadingRail,
            onRenderSpecAction: renderSpecActionInvoker,
            header: header,
            onBuild: onBuild,
            committedLayoutTransitionId:
                effectiveWindowLayout.activeLayoutTransitionId,
            admittedTopologySections:
                effectiveWindowLayout.admittedTopologySections,
            committedTopologyTransitionId:
                effectiveWindowLayout.activeTopologyTransitionId,
            clientIntentIdFactory: effectiveClientIntentIdFactory,
            onLayoutTransitionCommit: effectiveLayoutTransitionCommit,
            onLayoutTopologyCommit: effectiveLayoutTopologyCommit,
          )
        : InterfaceRuntimeShell.fromShellPanes(
            windowKey: effectiveWindowLayout.windowKey,
            layoutKey: effectiveWindowLayout.layoutKey,
            mode: effectiveWindowLayout.mode,
            sections: effectiveWindowLayout.sections,
            admittedSections: effectiveWindowLayout.admittedSections,
            shellPanes: threadLayoutShellPanes,
            materializedPaneStates: runtime.materializedPaneStates,
            allowedActions: hostState.allowedActions,
            panePackageRegistry: panePackageRegistry,
            renderSpecs:
                effectivePackageRuntime?.renderSpecs ?? dynamicRenderSpecs,
            renderComponentRegistry:
                effectivePackageRuntime?.renderComponentRegistry ??
                    const RenderComponentRegistry.empty(),
            mediaResolver: mediaResolver,
            leadingRail: leadingRail,
            onRenderSpecAction: renderSpecActionInvoker,
            header: header,
            onBuild: onBuild,
            committedLayoutTransitionId:
                effectiveWindowLayout.activeLayoutTransitionId,
            admittedTopologySections:
                effectiveWindowLayout.admittedTopologySections,
            committedTopologyTransitionId:
                effectiveWindowLayout.activeTopologyTransitionId,
            clientIntentIdFactory: effectiveClientIntentIdFactory,
            onLayoutTransitionCommit: effectiveLayoutTransitionCommit,
            onLayoutTopologyCommit: effectiveLayoutTopologyCommit,
          );

    return InterfacePaneApiScope(
      namespace: hostState.namespace,
      materializedPaneStates: runtime.materializedPaneStates,
      child: InterfaceRendererCapabilityHandshakeSync(
        rendererId: rendererId ?? hostState.namespace,
        rendererVersion: rendererVersion,
        interfacePackageRuntime: effectivePackageRuntime,
        child: InterfaceHostViewStateCacheLifecycleSync(
          hostState: hostState,
          child: runtimeShell,
        ),
      ),
    );
  }
}

EnvironmentNavigatorViewStateV1? _environmentNavigatorViewState(
  InterfaceRuntimeState runtime,
) {
  for (final state in runtime.materializedPaneStates) {
    if (!_materializedStateMatchesView(
      state,
      viewRef: _environmentNavigatorApiViewRef,
      projectionViewKey: _environmentNavigatorProjectionViewKey,
    )) {
      continue;
    }
    return EnvironmentNavigatorViewStateV1.fromJson(state.state);
  }
  return null;
}

ThreadLayoutViewStateV1? _threadLayoutViewState(InterfaceRuntimeState runtime) {
  for (final state in runtime.materializedPaneStates) {
    if (!_materializedStateMatchesView(
      state,
      viewRef: _threadLayoutApiViewRef,
      projectionViewKey: _threadLayoutProjectionViewKey,
    )) {
      continue;
    }
    return ThreadLayoutViewStateV1.fromJson(state.state);
  }
  return null;
}

List<InterfaceShellResolvedPane>? _shellPanesFromThreadLayout({
  required ThreadLayoutViewStateV1? threadLayout,
  required _HostWindowLayout windowLayout,
}) {
  if (threadLayout == null || threadLayout.sections.isEmpty) {
    return null;
  }
  return threadLayout.sections
      .where(
        (section) => _HostWindowLayout._boolValue(section.isVisible) ?? true,
      )
      .map(
        (section) => InterfaceShellResolvedPane(
          windowKey: windowLayout.windowKey,
          layoutKey: windowLayout.layoutKey,
          sectionKey: section.sectionKey,
          focusScopeId: section.focusScopeId,
          paneKind: _trimmedOrNull(section.paneKey) ??
              _trimmedOrNull(section.viewKey) ??
              section.sectionKey,
          viewRef: _trimmedOrNull(section.viewRef),
          projectionViewKey: _trimmedOrNull(section.viewKey),
          projectionViewId: _trimmedOrNull(section.viewKey),
          title: section.title,
          summary: _trimmedOrNull(section.description),
          stateSourceKind: 'host_pane_contribution',
        ),
      )
      .toList(growable: false);
}

UuidValue? _uuidValueOrNull(String? value) {
  final text = value?.trim();
  if (text == null || text.isEmpty) {
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

bool _materializedStateMatchesView(
  InterfaceMaterializedPaneState state, {
  required String viewRef,
  required String projectionViewKey,
}) {
  return _trimmedOrNull(state.projectionViewId) == projectionViewKey ||
      _stringFromMap(state.provenance, 'projection_view_key') ==
          projectionViewKey ||
      _stringFromMap(state.provenance, 'view_ref') == viewRef;
}

String? _stringFromMap(Map<String, dynamic> payload, String key) {
  final value = payload[key];
  if (value is! String) {
    return null;
  }
  return _trimmedOrNull(value);
}

class _HostWindowLayout {
  const _HostWindowLayout({
    required this.windowKey,
    required this.layoutKey,
    required this.mode,
    required this.sections,
    required this.admittedSections,
    required this.admittedTopologySections,
    this.activeLayoutTransitionId,
    this.activeTopologyTransitionId,
  });

  factory _HostWindowLayout.fromHostState(InterfaceHostState hostState) {
    final state = interfaceHostRuntimeWindowLayoutState(hostState);
    if (state != null) {
      final sections =
          state.sections.map(_buildSectionFromState).toList(growable: false);
      final admittedSections = state.admittedSections.isEmpty
          ? sections
          : state.admittedSections
              .map(_buildSectionFromState)
              .toList(growable: false);
      if (sections.isEmpty) {
        throw StateError('window_layout.sections is empty');
      }
      return _HostWindowLayout(
        windowKey: _stringValue(state.windowKey) ?? 'main',
        layoutKey: _stringValue(state.layoutKey) ?? 'unknown',
        mode: _windowLayoutMode(_stringValue(state.frameMode)),
        sections: sections,
        admittedSections: admittedSections,
        admittedTopologySections: _buildAdmittedTopologySectionsFromState(
          state,
          activeSections: sections,
        ),
        activeLayoutTransitionId: _stringValue(
          state.toJson()['active_layout_transition_id'],
        ),
        activeTopologyTransitionId: _stringValue(
          state.toJson()['active_topology_transition_id'],
        ),
      );
    }

    final payload = interfaceHostRuntimeWindowLayoutPayload(hostState);
    if (payload == null) {
      throw StateError('window_layout payload is missing');
    }
    final rawSections = payload['sections'];
    if (rawSections is! List) {
      throw StateError('window_layout.sections is missing');
    }
    final sections = rawSections
        .whereType<Map>()
        .map((item) => _buildSection(item.cast<String, dynamic>()))
        .toList(growable: false);
    if (sections.isEmpty) {
      throw StateError('window_layout.sections is empty');
    }
    final rawAdmittedSections = payload['admitted_sections'];
    final admittedSections = rawAdmittedSections is List
        ? rawAdmittedSections
            .whereType<Map>()
            .map((item) => _buildSection(item.cast<String, dynamic>()))
            .toList(growable: false)
        : sections;
    return _HostWindowLayout(
      windowKey: _stringValue(payload['window_key']) ?? 'main',
      layoutKey: _stringValue(payload['layout_key']) ?? 'unknown',
      mode: _windowLayoutMode(_stringValue(payload['frame_mode'])),
      sections: sections,
      admittedSections: admittedSections,
      admittedTopologySections: _buildAdmittedTopologySections(
        rawAdmittedSections is List ? rawAdmittedSections : rawSections,
      ),
      activeLayoutTransitionId: _stringValue(
        payload['active_layout_transition_id'],
      ),
      activeTopologyTransitionId: _stringValue(
        payload['active_topology_transition_id'],
      ),
    );
  }

  final String windowKey;
  final String layoutKey;
  final WindowLayoutMode mode;
  final List<InterfaceShellSection> sections;
  final List<InterfaceShellSection> admittedSections;
  final List<WindowLayoutTopologyCatalogSection> admittedTopologySections;
  final String? activeLayoutTransitionId;
  final String? activeTopologyTransitionId;

  static _HostWindowLayout? fromThreadLayoutOrNull(
    ThreadLayoutViewStateV1? threadLayout, {
    required _HostWindowLayout fallback,
  }) {
    if (threadLayout == null || threadLayout.sections.isEmpty) {
      return null;
    }
    final layoutKey =
        _stringValue(threadLayout.activeLayoutKey) ?? 'thread_layout';
    final topologyPinnedSectionKeys =
        fallback.activeTopologyTransitionId == null
            ? null
            : fallback.sections.map((section) => section.sectionKey).toSet();
    final sections = threadLayout.sections
        .where(
      (section) =>
          topologyPinnedSectionKeys == null ||
          topologyPinnedSectionKeys.contains(section.sectionKey),
    )
        .map(
      (section) {
        final mounted = fallback.sections.where(
          (candidate) => candidate.sectionKey == section.sectionKey,
        );
        final committed = mounted.isEmpty ? null : mounted.single;
        return InterfaceShellSection(
          sectionKey: section.sectionKey,
          region: _regionForSection(section.sectionKey),
          order: section.order,
          title: _stringValue(section.title) ??
              _titleFromSectionKey(section.sectionKey),
          flex: committed?.flex ?? section.flex,
          isVisible:
              committed?.isVisible ?? _boolValue(section.isVisible) ?? true,
          transitionSectionId: committed?.transitionSectionId,
          weightMicros: committed?.weightMicros,
          isCollapsed: committed?.isCollapsed ?? false,
        );
      },
    ).toList(growable: false);
    if (sections.isEmpty) {
      return null;
    }
    return _HostWindowLayout(
      windowKey: fallback.windowKey,
      layoutKey: layoutKey,
      mode: WindowLayoutMode.grid,
      sections: sections,
      admittedSections: fallback.admittedSections,
      admittedTopologySections: fallback.admittedTopologySections,
      activeLayoutTransitionId: fallback.activeLayoutTransitionId,
      activeTopologyTransitionId: fallback.activeTopologyTransitionId,
    );
  }

  static List<WindowLayoutTopologyCatalogSection>
      _buildAdmittedTopologySectionsFromState(
    InterfaceWindowLayoutState state, {
    required List<InterfaceShellSection> activeSections,
  }) {
    final admitted = state.toJson()['admitted_sections'];
    if (admitted is List && admitted.isNotEmpty) {
      return _buildAdmittedTopologySections(admitted);
    }
    return [
      for (final section in activeSections)
        if (section.transitionSectionId case final sectionId?)
          WindowLayoutTopologyCatalogSection(
            sectionId: sectionId,
            catalogOrder: section.order,
          ),
    ];
  }

  static List<WindowLayoutTopologyCatalogSection>
      _buildAdmittedTopologySections(List<dynamic> rows) {
    final sections = <WindowLayoutTopologyCatalogSection>[];
    for (final (index, row) in rows.indexed) {
      if (row is! Map) {
        continue;
      }
      final sectionId = _stringValue(
        row['layout_config_section_config_id'],
      );
      if (sectionId == null) {
        continue;
      }
      sections.add(
        WindowLayoutTopologyCatalogSection(
          sectionId: sectionId,
          catalogOrder: _intValue(row['order']) ?? index,
        ),
      );
    }
    return sections;
  }

  static InterfaceShellSection _buildSectionFromState(
    InterfaceWindowLayoutSectionState state,
  ) {
    final sectionKey = _stringValue(state.sectionKey) ?? 'unknown';
    final payload = state.toJson();
    return InterfaceShellSection(
      sectionKey: sectionKey,
      region: _regionForSection(sectionKey),
      order: state.order,
      title: _stringValue(state.title) ?? _titleFromSectionKey(sectionKey),
      flex: state.flex,
      isVisible: state.isVisible,
      transitionSectionId: _stringValue(
        payload['layout_config_section_config_id'],
      ),
      weightMicros: _intValue(payload['weight_micros']),
      isCollapsed: _boolValue(payload['is_collapsed']) ?? false,
    );
  }

  static InterfaceShellSection _buildSection(Map<String, dynamic> json) {
    final sectionKey = _stringValue(json['section_key']) ?? 'unknown';
    return InterfaceShellSection(
      sectionKey: sectionKey,
      region: _regionForSection(sectionKey),
      order: _intValue(json['order']) ?? 0,
      title: _stringValue(json['title']) ?? _titleFromSectionKey(sectionKey),
      flex: _doubleValue(json['flex']) ?? 1.0,
      isVisible: _boolValue(json['is_visible']) ?? true,
      transitionSectionId: _stringValue(
        json['layout_config_section_config_id'],
      ),
      weightMicros: _intValue(json['weight_micros']),
      isCollapsed: _boolValue(json['is_collapsed']) ?? false,
    );
  }

  static WindowLayoutMode _windowLayoutMode(String? rawMode) {
    return switch (rawMode) {
      'horizontal' => WindowLayoutMode.horizontal,
      'vertical' => WindowLayoutMode.vertical,
      'floating' => WindowLayoutMode.floating,
      _ => WindowLayoutMode.grid,
    };
  }

  static WindowFullscreenSectionRegion _regionForSection(String sectionKey) {
    return switch (sectionKey.trim().toLowerCase()) {
      'orchestration' ||
      'packages' ||
      'overlay_left' ||
      'navigation' =>
        WindowFullscreenSectionRegion.leading,
      'inspector' ||
      'overlay_right' ||
      'context' ||
      'details' =>
        WindowFullscreenSectionRegion.trailing,
      'console' ||
      'dock' ||
      'logs' ||
      'activity' =>
        WindowFullscreenSectionRegion.dock,
      _ => WindowFullscreenSectionRegion.stage,
    };
  }

  static String _titleFromSectionKey(String sectionKey) {
    return sectionKey
        .split('_')
        .where((part) => part.trim().isNotEmpty)
        .map(
          (part) =>
              '${part[0].toUpperCase()}${part.substring(1).toLowerCase()}',
        )
        .join(' ');
  }

  static String? _stringValue(Object? value) {
    final text = value is String ? value.trim() : '';
    return text.isEmpty ? null : text;
  }

  static int? _intValue(Object? value) {
    if (value is int) {
      return value;
    }
    if (value is num) {
      return value.toInt();
    }
    return int.tryParse('${value ?? ''}'.trim());
  }

  static double? _doubleValue(Object? value) {
    if (value is num) {
      return value.toDouble();
    }
    if (value is String) {
      return double.tryParse(value.trim());
    }
    return null;
  }

  static bool? _boolValue(Object? value) {
    if (value is bool) {
      return value;
    }
    final raw = '${value ?? ''}'.trim().toLowerCase();
    if (raw == 'true') {
      return true;
    }
    if (raw == 'false') {
      return false;
    }
    return null;
  }

  static _HostWindowLayout? fromHostStateOrNull(InterfaceHostState hostState) {
    try {
      return _HostWindowLayout.fromHostState(hostState);
    } on StateError {
      return null;
    }
  }
}

class _InterfaceHostRuntimeShellUnavailable extends StatelessWidget {
  const _InterfaceHostRuntimeShellUnavailable({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Text(
        message,
        style: theme.textTheme.bodyMedium?.copyWith(
          color: theme.colorScheme.onSurfaceVariant,
        ),
        textAlign: TextAlign.center,
      ),
    );
  }
}
