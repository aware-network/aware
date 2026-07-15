import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_interface_sdk/aware_interface_sdk.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';

import '../render_spec/pane_render_spec.dart';
import '../render_spec/pane_render_spec_renderer.dart';
import '../render_spec/render_component_registry.dart';
import 'shell_resolved_pane.dart';
import 'shell_section.dart';
import 'shell_scaffold.dart';

class InterfaceRuntimeShell extends StatelessWidget {
  InterfaceRuntimeShell({
    required this.windowKey,
    required this.layoutKey,
    required this.sections,
    required this.resolvedPanes,
    required this.panePackageRegistry,
    super.key,
    this.materializedPaneStates = const <InterfaceMaterializedPaneState>[],
    this.header,
    this.leadingRail,
    this.mode = WindowLayoutMode.grid,
    this.railSlots = const <WindowSlot>[],
    this.renderSpecs = const <PaneRenderSpec>[],
    this.renderComponentRegistry = const RenderComponentRegistry.empty(),
    this.mediaResolver,
    this.allowedActions = const <InterfaceAllowedAction>[],
    this.onRenderSpecAction,
    this.onRailSlotTapped,
    this.railSurfaceBuilder,
    this.onBuild,
    this.committedLayoutTransitionId,
    this.admittedTopologySections =
        const <WindowLayoutTopologyCatalogSection>[],
    this.admittedSections = const <InterfaceShellSection>[],
    this.committedTopologyTransitionId,
    this.clientIntentIdFactory,
    this.onLayoutTransitionCommit,
    this.onLayoutTopologyCommit,
  }) : shellPanes = resolvedPanes
            .map(InterfaceShellResolvedPane.fromDescriptor)
            .toList(growable: false);

  InterfaceRuntimeShell.fromShellPanes({
    required this.windowKey,
    required this.layoutKey,
    required this.sections,
    required this.shellPanes,
    required this.panePackageRegistry,
    super.key,
    this.materializedPaneStates = const <InterfaceMaterializedPaneState>[],
    this.header,
    this.leadingRail,
    this.mode = WindowLayoutMode.grid,
    this.railSlots = const <WindowSlot>[],
    this.renderSpecs = const <PaneRenderSpec>[],
    this.renderComponentRegistry = const RenderComponentRegistry.empty(),
    this.mediaResolver,
    this.allowedActions = const <InterfaceAllowedAction>[],
    this.onRenderSpecAction,
    this.onRailSlotTapped,
    this.railSurfaceBuilder,
    this.onBuild,
    this.committedLayoutTransitionId,
    this.admittedTopologySections =
        const <WindowLayoutTopologyCatalogSection>[],
    this.admittedSections = const <InterfaceShellSection>[],
    this.committedTopologyTransitionId,
    this.clientIntentIdFactory,
    this.onLayoutTransitionCommit,
    this.onLayoutTopologyCommit,
  }) : resolvedPanes = const <InterfaceResolvedPaneDescriptor>[];

  final String windowKey;
  final String layoutKey;
  final List<InterfaceShellSection> sections;
  final List<InterfaceResolvedPaneDescriptor> resolvedPanes;
  final List<InterfaceShellResolvedPane> shellPanes;
  final List<InterfaceMaterializedPaneState> materializedPaneStates;
  final PanePackageRegistry panePackageRegistry;
  final Widget? header;
  final Widget? leadingRail;
  final WindowLayoutMode mode;
  final List<WindowSlot> railSlots;
  final List<PaneRenderSpec> renderSpecs;
  final RenderComponentRegistry renderComponentRegistry;
  final InterfaceStorageMediaResolver? mediaResolver;
  final List<InterfaceAllowedAction> allowedActions;
  final PaneRenderActionInvoker? onRenderSpecAction;
  final ValueChanged<WindowSlot>? onRailSlotTapped;
  final InterfaceShellRailSurfaceBuilder? railSurfaceBuilder;
  final ValueChanged<String>? onBuild;
  final String? committedLayoutTransitionId;
  final List<WindowLayoutTopologyCatalogSection> admittedTopologySections;
  final List<InterfaceShellSection> admittedSections;
  final String? committedTopologyTransitionId;
  final String Function()? clientIntentIdFactory;
  final WindowLayoutTransitionCommitCallback? onLayoutTransitionCommit;
  final WindowLayoutTopologyCommitCallback? onLayoutTopologyCommit;

  @override
  Widget build(BuildContext context) {
    onBuild?.call('InterfaceRuntimeShell');
    final index = _InterfaceRuntimeShellIndex(
      windowKey: windowKey,
      layoutKey: layoutKey,
      shellPanes: shellPanes,
      materializedPaneStates: materializedPaneStates,
      renderSpecs: renderSpecs,
    );
    final frameSections = sections
        .map((section) => _buildSection(section, index))
        .toList(growable: false);
    final admittedFrameSections = admittedSections
        .map((section) => _buildSection(section, index))
        .toList(growable: false);

    return InterfaceShellScaffold(
      header: header,
      leadingRail: leadingRail,
      mode: mode,
      railSlots: railSlots,
      onRailSlotTapped: onRailSlotTapped,
      railSurfaceBuilder: railSurfaceBuilder,
      contentPadding: EdgeInsets.zero,
      framePadding: EdgeInsets.zero,
      sections: frameSections,
      admittedSectionFrames: admittedFrameSections,
      committedLayoutTransitionId: committedLayoutTransitionId,
      admittedTopologySections: admittedTopologySections,
      committedTopologyTransitionId: committedTopologyTransitionId,
      clientIntentIdFactory: clientIntentIdFactory,
      onLayoutTransitionCommit: onLayoutTransitionCommit,
      onLayoutTopologyCommit: onLayoutTopologyCommit,
    );
  }

  WindowFullscreenSectionFrameSection _buildSection(
    InterfaceShellSection section,
    _InterfaceRuntimeShellIndex index,
  ) {
    final mountedPanes = index.panesForSection(section.sectionKey);

    return WindowFullscreenSectionFrameSection(
      id: section.sectionKey,
      region: section.region,
      order: section.order,
      flex: section.flex,
      transitionSectionId: section.transitionSectionId,
      weightMicros: section.weightMicros,
      isVisible: section.isVisible,
      isCollapsed: section.isCollapsed,
      child: _InterfaceRuntimeShellSectionCard(
        title: section.title ?? section.sectionKey,
        showTitle: _sectionShouldShowTitle(mountedPanes, index),
        child: mountedPanes.isEmpty
            ? _InterfaceRuntimeShellEmptySection(
                sectionKey: section.sectionKey,
                layoutKey: layoutKey,
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (var paneIndex = 0;
                      paneIndex < mountedPanes.length;
                      paneIndex++) ...[
                    _buildPaneSurface(
                      mountedPanes[paneIndex],
                      index: index,
                    ),
                    if (paneIndex < mountedPanes.length - 1)
                      const SizedBox(height: 12),
                  ],
                ],
              ),
      ),
    );
  }

  bool _sectionShouldShowTitle(
    List<InterfaceShellResolvedPane> mountedPanes,
    _InterfaceRuntimeShellIndex index,
  ) {
    if (mountedPanes.length != 1) {
      return true;
    }
    return !_paneHasRenderSpec(mountedPanes.single, index);
  }

  bool _paneHasRenderSpec(
    InterfaceShellResolvedPane pane,
    _InterfaceRuntimeShellIndex index,
  ) {
    return index.renderSpecForPane(pane) != null;
  }

  Widget _buildPaneSurface(
    InterfaceShellResolvedPane pane, {
    required _InterfaceRuntimeShellIndex index,
  }) {
    final materializedState = index.materializedStateForPane(pane);
    final paneStateKey = materializedState?.paneStateKey ??
        _InterfaceRuntimeShellIndex.paneStateKeyForPane(pane);
    final viewKey = _trimmedOrNull(pane.projectionViewKey) ??
        _trimmedOrNull(pane.projectionViewId);
    final viewRef = _trimmedOrNull(pane.viewRef);
    final paneContext = _paneContextForPane(
      pane: pane,
      materializedState: materializedState,
      paneStateKey: paneStateKey,
      viewKey: viewKey,
      viewRef: viewRef,
    );

    final renderSpec = index.renderSpecForPane(pane);
    if (renderSpec != null) {
      return PaneRenderSpecWidget(
        spec: renderSpec,
        paneContext: paneContext,
        materializedState: materializedState,
        onInvokeAction: onRenderSpecAction,
        mediaResolver: mediaResolver,
        renderComponentRegistry: renderComponentRegistry,
        onBuild: onBuild,
      );
    }

    if (pane.stateSourceKind == 'host_pane_contribution') {
      return _InterfaceRuntimeShellHostContributionPane(
        pane: pane,
        paneContext: paneContext,
        allowedActions: allowedActions,
        onInvokeAction: onRenderSpecAction,
      );
    }

    final panePackageId = pane.panePackageId;
    if (panePackageId == null) {
      return _InterfaceRuntimeShellPlaceholder(
        title: pane.title ?? pane.paneKind,
        message:
            'Pane package identity is missing for `${pane.paneKind}`. Runtime shell cannot mount this pane yet.',
      );
    }

    final built = panePackageRegistry.build(panePackageId, paneContext);

    if (built == null) {
      return _InterfaceRuntimeShellPlaceholder(
        title: pane.title ?? pane.paneKind,
        message:
            'Pane package `${pane.panePackageName ?? panePackageId.uuid}` is not registered in the Dart pane runtime.',
      );
    }

    return built;
  }

  PaneContext _paneContextForPane({
    required InterfaceShellResolvedPane pane,
    required InterfaceMaterializedPaneState? materializedState,
    required String paneStateKey,
    required String? viewKey,
    required String? viewRef,
  }) {
    return PaneContext(
      paneId: pane.paneConfigId?.uuid ?? '${pane.sectionKey}:${pane.paneKind}',
      kind: pane.paneKind,
      parameters: <String, dynamic>{
        'windowKey': pane.windowKey,
        'layoutKey': pane.layoutKey,
        'sectionKey': pane.sectionKey,
        'projectionViewId': pane.projectionViewId,
        'viewRef': pane.viewRef,
        'projectionViewKey': pane.projectionViewKey,
        'stateSourceKind': pane.stateSourceKind,
        'stateProjectionHash': pane.stateProjectionHash,
        kPaneParamWindowKey: pane.windowKey,
        kPaneParamLayoutKey: pane.layoutKey,
        kPaneParamSectionKey: pane.sectionKey,
        kPaneParamFocusScopeId: pane.focusScopeId?.uuid,
        kPaneParamBranchId: pane.branchId?.uuid,
        if (viewRef != null) kPaneParamViewRef: viewRef,
        if (viewKey != null) kPaneParamViewKey: viewKey,
        kPaneParamStateProjectionHash: pane.stateProjectionHash,
        kPaneParamPaneStateKey: paneStateKey,
        if (materializedState != null)
          kPaneParamMaterializedState: materializedState,
      },
      metadata: <String, Object?>{
        kPaneMetadataWindowSectionId: pane.sectionKey,
      },
    );
  }
}

class _InterfaceRuntimeShellIndex {
  _InterfaceRuntimeShellIndex({
    required this.windowKey,
    required this.layoutKey,
    required List<InterfaceShellResolvedPane> shellPanes,
    required List<InterfaceMaterializedPaneState> materializedPaneStates,
    required List<PaneRenderSpec> renderSpecs,
  }) : _materializedPaneStates = materializedPaneStates {
    for (final pane in shellPanes) {
      if (pane.windowKey != windowKey || pane.layoutKey != layoutKey) {
        continue;
      }
      final key = _sectionKey(pane.sectionKey);
      (_panesBySection[key] ??= <InterfaceShellResolvedPane>[]).add(pane);
    }
    for (final state in materializedPaneStates) {
      if (state.paneStateKey.trim().isNotEmpty) {
        _stateByPaneStateKey[state.paneStateKey] = state;
      }
    }
    for (final spec in renderSpecs) {
      final key = _normalized(spec.paneKind);
      if (key == null) {
        continue;
      }
      (_renderSpecsByPaneKind[key] ??= <PaneRenderSpec>[]).add(spec);
    }
  }

  final String windowKey;
  final String layoutKey;
  final List<InterfaceMaterializedPaneState> _materializedPaneStates;
  final Map<String, List<InterfaceShellResolvedPane>> _panesBySection =
      <String, List<InterfaceShellResolvedPane>>{};
  final Map<String, InterfaceMaterializedPaneState> _stateByPaneStateKey =
      <String, InterfaceMaterializedPaneState>{};
  final Map<String, List<PaneRenderSpec>> _renderSpecsByPaneKind =
      <String, List<PaneRenderSpec>>{};

  List<InterfaceShellResolvedPane> panesForSection(String sectionKey) {
    final panes = _panesBySection[_sectionKey(sectionKey)];
    if (panes == null || panes.isEmpty) {
      return const <InterfaceShellResolvedPane>[];
    }
    return List<InterfaceShellResolvedPane>.unmodifiable(panes);
  }

  PaneRenderSpec? renderSpecForPane(InterfaceShellResolvedPane pane) {
    final candidates = _renderSpecsByPaneKind[_normalized(pane.paneKind)];
    if (candidates == null || candidates.isEmpty) {
      return null;
    }
    final match = InterfaceShellPaneMatch(
      paneKind: pane.paneKind,
      viewRef: _trimmedOrNull(pane.viewRef),
      projectionViewKey: _trimmedOrNull(pane.projectionViewKey) ??
          _trimmedOrNull(pane.projectionViewId),
    );
    for (final spec in candidates) {
      if (spec.matchesPane(match)) {
        return spec;
      }
    }
    return null;
  }

  InterfaceMaterializedPaneState? materializedStateForPane(
    InterfaceShellResolvedPane pane,
  ) {
    final direct = _stateByPaneStateKey[paneStateKeyForPane(pane)];
    if (direct != null) {
      return direct;
    }
    for (final state in _materializedPaneStates) {
      if (_materializedStateMatchesPane(state, pane)) {
        return state;
      }
    }
    return null;
  }

  static String paneStateKeyForPane(InterfaceShellResolvedPane pane) {
    return [
      pane.windowKey,
      pane.layoutKey,
      pane.sectionKey,
      pane.paneKind,
      pane.paneConfigId?.uuid ?? '',
      pane.stateProjectionHash ?? '',
    ].join(':');
  }

  static bool _materializedStateMatchesPane(
    InterfaceMaterializedPaneState state,
    InterfaceShellResolvedPane pane,
  ) {
    if (state.windowKey != pane.windowKey ||
        state.layoutKey != pane.layoutKey ||
        state.sectionKey != pane.sectionKey ||
        state.paneKind != pane.paneKind) {
      return false;
    }
    final paneConfigId = pane.paneConfigId?.uuid;
    if (paneConfigId != null && state.paneConfigId?.uuid != paneConfigId) {
      return false;
    }
    final branchId = pane.branchId?.uuid;
    if (branchId != null && state.branchId?.uuid != branchId) {
      return false;
    }
    return true;
  }

  static String _sectionKey(String value) => value.trim().toLowerCase();
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

String? _normalized(String? value) => _trimmedOrNull(value)?.toLowerCase();

class _InterfaceRuntimeShellSectionCard extends StatelessWidget {
  const _InterfaceRuntimeShellSectionCard({
    required this.title,
    required this.child,
    this.showTitle = true,
  });

  final String title;
  final Widget child;
  final bool showTitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LayoutBuilder(
      builder: (context, constraints) {
        final hasBoundedHeight = constraints.hasBoundedHeight;
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withValues(
              alpha: 0.55,
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (showTitle) ...[
                Text(title, style: theme.textTheme.titleMedium),
                const SizedBox(height: 12),
              ],
              if (hasBoundedHeight)
                Expanded(child: SingleChildScrollView(child: child))
              else
                child,
            ],
          ),
        );
      },
    );
  }
}

class _InterfaceRuntimeShellEmptySection extends StatelessWidget {
  const _InterfaceRuntimeShellEmptySection({
    required this.sectionKey,
    required this.layoutKey,
  });

  final String sectionKey;
  final String layoutKey;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Text(
      'No mounted panes for section `$sectionKey` in layout `$layoutKey`.',
      style: theme.textTheme.bodyMedium?.copyWith(
        color: theme.colorScheme.onSurfaceVariant,
      ),
    );
  }
}

class _InterfaceRuntimeShellPlaceholder extends StatelessWidget {
  const _InterfaceRuntimeShellPlaceholder({
    required this.title,
    required this.message,
  });

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          Text(
            message,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _InterfaceRuntimeShellHostContributionPane extends StatefulWidget {
  const _InterfaceRuntimeShellHostContributionPane({
    required this.pane,
    required this.paneContext,
    required this.allowedActions,
    required this.onInvokeAction,
  });

  final InterfaceShellResolvedPane pane;
  final PaneContext paneContext;
  final List<InterfaceAllowedAction> allowedActions;
  final PaneRenderActionInvoker? onInvokeAction;

  @override
  State<_InterfaceRuntimeShellHostContributionPane> createState() =>
      _InterfaceRuntimeShellHostContributionPaneState();
}

class _InterfaceRuntimeShellHostContributionPaneState
    extends State<_InterfaceRuntimeShellHostContributionPane> {
  final Set<String> _pendingActionKeys = <String>{};
  final Map<String, String> _actionErrors = <String, String>{};

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final title = _trimmedOrNull(widget.pane.title) ?? widget.pane.paneKind;
    final summary = _trimmedOrNull(widget.pane.summary);
    final narrative = _trimmedOrNull(widget.pane.narrativeKey);
    final actions = _hostContributionActions();
    final sharedDisabledReason = _sharedDisabledReason(actions);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          children: <Widget>[
            Expanded(child: Text(title, style: theme.textTheme.titleSmall)),
            _HostContributionBadge(label: widget.pane.stateSourceKind),
          ],
        ),
        if (summary != null) ...<Widget>[
          const SizedBox(height: 8),
          Text(
            summary,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
        if (actions.isNotEmpty) ...<Widget>[
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              for (final action in actions)
                FilledButton.tonal(
                  onPressed: action.enabled &&
                          widget.onInvokeAction != null &&
                          !_pendingActionKeys.contains(action.actionKey)
                      ? () => _invoke(action)
                      : null,
                  child: Text(
                    _pendingActionKeys.contains(action.actionKey)
                        ? 'Working'
                        : action.label,
                  ),
                ),
            ],
          ),
          if (sharedDisabledReason != null) ...<Widget>[
            const SizedBox(height: 8),
            Text(
              sharedDisabledReason,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
          for (final action in actions)
            if (_actionDetail(action, sharedDisabledReason) !=
                null) ...<Widget>[
              const SizedBox(height: 6),
              Text(
                _actionDetail(action, sharedDisabledReason)!,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
        ],
        if (narrative != null) ...<Widget>[
          const SizedBox(height: 12),
          Text(
            narrative,
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ],
    );
  }

  List<_HostContributionAction> _hostContributionActions() {
    final actionsByKey = <String, InterfaceAllowedAction>{
      for (final action in widget.allowedActions) action.actionKey: action,
    };
    return widget.pane.actionKeys.map((actionKey) {
      final action = actionsByKey[actionKey];
      return _HostContributionAction(
        actionKey: actionKey,
        label: _trimmedOrNull(action?.label) ?? actionKey,
        enabled: action?.enabled ?? false,
        reason: action?.reason,
        error: _actionErrors[actionKey],
      );
    }).toList(growable: false);
  }

  String? _sharedDisabledReason(List<_HostContributionAction> actions) {
    final disabledReasons = <String>{};
    var disabledReasonCount = 0;
    for (final action in actions) {
      if (action.enabled || _trimmedOrNull(action.error) != null) {
        continue;
      }
      final reason = _trimmedOrNull(action.reason);
      if (reason == null) {
        continue;
      }
      disabledReasonCount += 1;
      disabledReasons.add(reason);
    }
    if (disabledReasonCount > 1 && disabledReasons.length == 1) {
      return disabledReasons.single;
    }
    return null;
  }

  String? _actionDetail(
    _HostContributionAction action,
    String? sharedDisabledReason,
  ) {
    final error = _trimmedOrNull(action.error);
    if (error != null) {
      return error;
    }
    final reason = _trimmedOrNull(action.reason);
    if (reason != null && reason != sharedDisabledReason) {
      return reason;
    }
    return null;
  }

  Future<void> _invoke(_HostContributionAction action) async {
    final invoker = widget.onInvokeAction;
    if (invoker == null || _pendingActionKeys.contains(action.actionKey)) {
      return;
    }
    setState(() {
      _pendingActionKeys.add(action.actionKey);
      _actionErrors.remove(action.actionKey);
    });
    try {
      await invoker(
        PaneRenderActionInvocation(
          paneContext: widget.paneContext,
          actionBinding: PaneActionBinding(
            bindingKey: action.actionKey,
            event: kPaneRenderActionEventActivate,
            actionKey: action.actionKey,
            actionKind: kPaneRenderActionKindAction,
            label: action.label,
          ),
          payload: const <String, dynamic>{},
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _actionErrors[action.actionKey] = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _pendingActionKeys.remove(action.actionKey);
        });
      }
    }
  }
}

class _HostContributionAction {
  const _HostContributionAction({
    required this.actionKey,
    required this.label,
    required this.enabled,
    this.reason,
    this.error,
  });

  final String actionKey;
  final String label;
  final bool enabled;
  final String? reason;
  final String? error;
}

class _HostContributionBadge extends StatelessWidget {
  const _HostContributionBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer.withValues(alpha: 0.48),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSecondaryContainer,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
