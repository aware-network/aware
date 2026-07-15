import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;

import 'pane_kind.dart';
import 'pane_selection_context.dart';

/// Metadata key used to pass window header controller arguments to panes.
const String kPaneMetadataWindowHeaderArgs = 'windowHeaderArgs';

/// Metadata key used to pass the window section identifier to panes.
const String kPaneMetadataWindowSectionId = 'windowSectionId';

/// Metadata key used to pass the base window pane identifier to panes.
const String kPaneMetadataWindowPaneId = 'windowPaneId';

/// Metadata key used to pass the selection context through runtime metadata.
const String kPaneMetadataSelectionContext =
    'awarePaneRuntime.selectionContext';

/// Metadata key used to expose a window overlay delegate to panes.
const String kPaneMetadataWindowOverlayDelegate = 'windowOverlayDelegate';

/// Parameter key for the resolved `ObjectProjectionGraphIdentity.key`.
///
/// v0: provided by the host shell after resolving FocusScope.view.
/// v1+: expected to be provided by bundle-provided view registries.
const String kPaneParamOpgIdentityKey = 'awarePaneRuntime.opgIdentityKey';

/// Parameter key for the resolved `ObjectProjectionGraphView.view_key`.
///
/// This is the canonical "view selector" within a projection family.
const String kPaneParamViewKey = 'awarePaneRuntime.viewKey';

/// Parameter key for the resolved ProjectionExperienceView reference.
///
/// This is the canonical experience view contract identity, for example
/// `aware_conversations.chat.home.v1`.
const String kPaneParamViewRef = 'awarePaneRuntime.viewRef';

/// Parameter key for the stable Interface Host materialized pane-state key.
const String kPaneParamPaneStateKey = 'awarePaneRuntime.paneStateKey';

/// Parameter key for the host-published materialized pane state object.
const String kPaneParamMaterializedState = 'awarePaneRuntime.materializedState';

/// Parameter key for the resolved Interface window key.
const String kPaneParamWindowKey = 'awarePaneRuntime.windowKey';

/// Parameter key for the resolved Interface layout key.
const String kPaneParamLayoutKey = 'awarePaneRuntime.layoutKey';

/// Parameter key for the resolved Interface section key.
const String kPaneParamSectionKey = 'awarePaneRuntime.sectionKey';

/// Parameter key for the resolved FocusScope id.
const String kPaneParamFocusScopeId = 'awarePaneRuntime.focusScopeId';

/// Parameter key for the resolved lane branch id.
const String kPaneParamBranchId = 'awarePaneRuntime.branchId';

/// Parameter key for the resolved state projection hash.
const String kPaneParamStateProjectionHash =
    'awarePaneRuntime.stateProjectionHash';

/// Context information passed to pane builders.
class PaneContext {
  PaneContext({
    required this.paneId,
    required this.kind,
    this.projectId,
    this.selectedNodeId,
    Map<String, dynamic>? parameters,
    Map<String, Object?>? metadata,
    this.instanceId,
    this.onClose,
    this.selectionContext,
  }) : parameters = parameters ?? <String, dynamic>{},
       metadata = metadata ?? <String, Object?>{};

  final String paneId;
  final PaneKey kind;
  final String? projectId;
  final String? selectedNodeId;
  final Map<String, dynamic> parameters;
  final Map<String, Object?> metadata;
  final String? instanceId;
  final VoidCallback? onClose;
  final PaneSelectionContext? selectionContext;

  PaneContext copyWith({
    String? paneId,
    PaneKey? kind,
    String? projectId,
    String? selectedNodeId,
    Map<String, dynamic>? parameters,
    Map<String, Object?>? metadata,
    String? instanceId,
    VoidCallback? onClose,
    PaneSelectionContext? selectionContext,
    bool clearSelectionContext = false,
  }) {
    return PaneContext(
      paneId: paneId ?? this.paneId,
      kind: kind ?? this.kind,
      projectId: projectId ?? this.projectId,
      selectedNodeId: selectedNodeId ?? this.selectedNodeId,
      parameters: parameters ?? Map<String, dynamic>.from(this.parameters),
      metadata: metadata ?? Map<String, Object?>.from(this.metadata),
      instanceId: instanceId ?? this.instanceId,
      onClose: onClose ?? this.onClose,
      selectionContext: clearSelectionContext
          ? null
          : selectionContext ?? this.selectionContext,
    );
  }
}

/// Pane builder function signature.
typedef PaneBuilder =
    Widget Function(BuildContext context, WidgetRef ref, PaneContext ctx);

/// Interface for modules to expose their panes.
abstract class PaneProvider {
  /// Module identifier.
  String get moduleId;

  /// Pane kinds this provider can handle.
  List<PaneKey> get supportedPanes;

  /// Get a pane builder for the given kind.
  PaneBuilder? getBuilder(PaneKey kind);

  /// Get display information for a pane kind.
  PaneDisplayInfo getDisplayInfo(PaneKey kind);
}

/// Display information delegates to the shared aware_pane type.
typedef PaneDisplayInfo = runtime.PaneDisplayInfo;

/// Alias the shared runtime implementation so host code continues to depend on
/// a single PaneBus definition sourced from aware_pane.
typedef PaneBus = runtime.PaneBus;
