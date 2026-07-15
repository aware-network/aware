import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';

typedef InterfaceShellRailSurfaceBuilder = Widget Function(
    BuildContext context, Widget child);

/// Common Flutter shell scaffold owned by Interface representation.
///
/// This stays deliberately below runtime descriptor and pane-package mounting
/// concerns. It is the shared shell/chrome target that later phases will feed
/// from canonical runtime truth.
class InterfaceShellScaffold extends StatefulWidget {
  InterfaceShellScaffold({
    required this.sections,
    super.key,
    this.header,
    this.leadingRail,
    this.railSlots = const <WindowSlot>[],
    this.onRailSlotTapped,
    this.railSurfaceBuilder,
    this.mode = WindowLayoutMode.grid,
    this.contentPadding = const EdgeInsets.all(12),
    this.framePadding = const EdgeInsets.fromLTRB(28, 24, 28, 32),
    this.railPadding = const EdgeInsets.only(top: 12, left: 4, bottom: 12),
    this.maxContentWidth = double.infinity,
    this.sectionSpacing = 18,
    this.columnSpacing = 20,
    this.wideBreakpoint = 1080,
    this.leadingRailWidth = 280,
    this.trailingRailWidth = 360,
    this.dockHeight = 108,
    this.dockSpansLeadingRail = true,
    this.useViewportShellOnWide = true,
    this.backgroundColor = Colors.transparent,
    this.committedLayoutTransitionId,
    this.admittedTopologySections =
        const <WindowLayoutTopologyCatalogSection>[],
    this.admittedSectionFrames = const <WindowFullscreenSectionFrameSection>[],
    this.committedTopologyTransitionId,
    this.clientIntentIdFactory,
    this.onLayoutTransitionCommit,
    this.onLayoutTopologyCommit,
  }) : assert(
          railSlots.isEmpty || onRailSlotTapped != null,
          'onRailSlotTapped must be provided when railSlots are present.',
        );

  final Widget? header;
  final Widget? leadingRail;
  final List<WindowFullscreenSectionFrameSection> sections;
  final List<WindowSlot> railSlots;
  final ValueChanged<WindowSlot>? onRailSlotTapped;
  final InterfaceShellRailSurfaceBuilder? railSurfaceBuilder;
  final WindowLayoutMode mode;
  final EdgeInsets contentPadding;
  final EdgeInsets framePadding;
  final EdgeInsets railPadding;
  final double maxContentWidth;
  final double sectionSpacing;
  final double columnSpacing;
  final double wideBreakpoint;
  final double leadingRailWidth;
  final double trailingRailWidth;
  final double dockHeight;
  final bool dockSpansLeadingRail;
  final bool useViewportShellOnWide;
  final Color backgroundColor;
  final String? committedLayoutTransitionId;
  final List<WindowLayoutTopologyCatalogSection> admittedTopologySections;
  final List<WindowFullscreenSectionFrameSection> admittedSectionFrames;
  final String? committedTopologyTransitionId;
  final String Function()? clientIntentIdFactory;
  final WindowLayoutTransitionCommitCallback? onLayoutTransitionCommit;
  final WindowLayoutTopologyCommitCallback? onLayoutTopologyCommit;

  @override
  State<InterfaceShellScaffold> createState() => _InterfaceShellScaffoldState();
}

class _InterfaceShellScaffoldState extends State<InterfaceShellScaffold> {
  WindowLayoutTransitionController? _layoutTransitionController;
  WindowLayoutTopologyTransitionController? _topologyTransitionController;
  String? _committedSignature;
  String? _committedTopologySignature;

  @override
  void initState() {
    super.initState();
    _configureTopologyTransitionController();
    _configureLayoutTransitionController();
  }

  @override
  void didUpdateWidget(covariant InterfaceShellScaffold oldWidget) {
    super.didUpdateWidget(oldWidget);
    final nextTopologySignature = _layoutTopologySignature();
    final shouldEnableTopology = _layoutTopologyTransitionEnabled;
    if ((_topologyTransitionController != null) != shouldEnableTopology) {
      _configureTopologyTransitionController();
    } else if (shouldEnableTopology &&
        nextTopologySignature != _committedTopologySignature) {
      _committedTopologySignature = nextTopologySignature;
      _topologyTransitionController!.reconcile(
        admittedSections: widget.admittedTopologySections,
        committedActiveSectionIds: _committedActiveTopologyIds(),
        committedTopologyTransitionId: widget.committedTopologyTransitionId,
      );
    }
    final nextSignature = _layoutTransitionSignature();
    final shouldEnable = _layoutTransitionEnabled;
    if ((_layoutTransitionController != null) != shouldEnable) {
      _configureLayoutTransitionController();
      return;
    }
    if (shouldEnable && nextSignature != _committedSignature) {
      _committedSignature = nextSignature;
      _layoutTransitionController!.reconcile(
        committedSections: _committedVector(),
        committedTransitionId: widget.committedLayoutTransitionId,
        committedTopologyTransitionId: widget.committedTopologyTransitionId,
      );
    }
  }

  @override
  void dispose() {
    _layoutTransitionController?.dispose();
    _topologyTransitionController?.dispose();
    super.dispose();
  }

  bool get _layoutTopologyTransitionEnabled {
    if (widget.onLayoutTopologyCommit == null ||
        widget.clientIntentIdFactory == null ||
        widget.admittedTopologySections.isEmpty ||
        widget.sections.isEmpty) {
      return false;
    }
    final activeIds = _committedActiveTopologyIds();
    final admittedIds = widget.admittedTopologySections
        .map((section) => section.sectionId)
        .toSet();
    return activeIds.length == widget.sections.length &&
        activeIds.every(admittedIds.contains);
  }

  bool get _layoutTransitionEnabled {
    if (widget.onLayoutTransitionCommit == null ||
        widget.clientIntentIdFactory == null ||
        widget.sections.isEmpty) {
      return false;
    }
    final ids = <String>{};
    for (final section in widget.sections) {
      final id = section.transitionSectionId?.trim();
      if (id == null || id.isEmpty || !ids.add(id)) {
        return false;
      }
    }
    return true;
  }

  void _configureLayoutTransitionController() {
    _layoutTransitionController?.dispose();
    _layoutTransitionController = null;
    _committedSignature = _layoutTransitionSignature();
    if (!_layoutTransitionEnabled) {
      return;
    }
    _layoutTransitionController = WindowLayoutTransitionController(
      committedSections: _committedVector(),
      committedTransitionId: widget.committedLayoutTransitionId,
      committedTopologyTransitionId: widget.committedTopologyTransitionId,
      clientIntentIdFactory: widget.clientIntentIdFactory!,
      onCommit: widget.onLayoutTransitionCommit!,
    )..addListener(_onLayoutTransitionChanged);
  }

  void _configureTopologyTransitionController() {
    _topologyTransitionController?.dispose();
    _topologyTransitionController = null;
    _committedTopologySignature = _layoutTopologySignature();
    if (!_layoutTopologyTransitionEnabled) {
      return;
    }
    _topologyTransitionController = WindowLayoutTopologyTransitionController(
      admittedSections: widget.admittedTopologySections,
      committedActiveSectionIds: _committedActiveTopologyIds(),
      committedTopologyTransitionId: widget.committedTopologyTransitionId,
      clientIntentIdFactory: widget.clientIntentIdFactory!,
      onCommit: widget.onLayoutTopologyCommit!,
    )..addListener(_onLayoutTransitionChanged);
  }

  void _onLayoutTransitionChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  List<WindowLayoutSectionVectorState> _committedVector() {
    return [
      for (final section in widget.sections)
        WindowLayoutSectionVectorState(
          sectionId: section.transitionSectionId!.trim(),
          order: section.order,
          weight: section.weightMicros != null
              ? section.weightMicros! / windowLayoutWeightMicrosTotal
              : section.flex,
          weightMicros: section.weightMicros,
          isVisible: section.isVisible,
          isCollapsed: section.isCollapsed,
        ),
    ];
  }

  List<String> _committedActiveTopologyIds() => [
        for (final section in widget.sections)
          if (section.transitionSectionId?.trim() case final sectionId?
              when sectionId.isNotEmpty)
            sectionId,
      ];

  String? _layoutTransitionSignature() {
    if (!_layoutTransitionEnabled) {
      return null;
    }
    return <String>[
      widget.committedLayoutTransitionId ?? '',
      widget.committedTopologyTransitionId ?? '',
      for (final section in widget.sections)
        '${section.transitionSectionId}:${section.order}:${section.weightMicros}:${section.flex}:${section.isVisible}:${section.isCollapsed}',
    ].join('|');
  }

  String? _layoutTopologySignature() {
    if (!_layoutTopologyTransitionEnabled) {
      return null;
    }
    return <String>[
      widget.committedTopologyTransitionId ?? '',
      for (final section in widget.admittedTopologySections)
        '${section.sectionId}:${section.catalogOrder}',
      'active=${_committedActiveTopologyIds().join(',')}',
    ].join('|');
  }

  List<WindowFullscreenSectionFrameSection> _effectiveSections() {
    final topologyController = _topologyTransitionController;
    final topologyOrder = topologyController == null
        ? null
        : <String, int>{
            for (var index = 0;
                index < topologyController.activeSectionIds.length;
                index += 1)
              topologyController.activeSectionIds[index]: index,
          };
    final topologyFrameById = <String, WindowFullscreenSectionFrameSection>{
      for (final section in widget.admittedSectionFrames)
        if (section.transitionSectionId case final sectionId?)
          sectionId: section,
      for (final section in widget.sections)
        if (section.transitionSectionId case final sectionId?)
          sectionId: section,
    };
    final topologySections = topologyOrder == null
        ? widget.sections
        : <WindowFullscreenSectionFrameSection>[
            for (final entry in topologyOrder.entries)
              if (topologyFrameById[entry.key] case final section?)
                section.copyWith(order: entry.value),
          ];
    final controller = _layoutTransitionController;
    if (controller == null) {
      return topologySections;
    }
    final previewById = {
      for (final section in controller.sections) section.sectionId: section,
    };
    return [
      for (final section in topologySections)
        if (previewById[section.transitionSectionId] case final preview?)
          section.copyWith(
            flex: preview.weight,
            weightMicros: preview.weightMicros,
            isVisible: preview.isVisible,
            isCollapsed: preview.isCollapsed,
          )
        else
          section,
    ];
  }

  @override
  Widget build(BuildContext context) {
    final frame = WindowFullscreenSectionFrame(
      header: widget.header,
      sections: _effectiveSections(),
      mode: widget.mode,
      maxContentWidth: widget.maxContentWidth,
      padding: widget.framePadding,
      sectionSpacing: widget.sectionSpacing,
      columnSpacing: widget.columnSpacing,
      wideBreakpoint: widget.wideBreakpoint,
      leadingRailWidth: widget.leadingRailWidth,
      trailingRailWidth: widget.trailingRailWidth,
      dockHeight: widget.dockHeight,
      dockSpansLeadingRail: widget.dockSpansLeadingRail,
      useViewportShellOnWide: widget.useViewportShellOnWide,
      onResizeStart: _topologyTransitionController?.previewing == true
          ? null
          : _layoutTransitionController?.beginPreview,
      onResizeUpdate: (leadingIds, trailingIds, deltaFraction) {
        _layoutTransitionController?.previewResizeGroups(
          leadingSectionIds: leadingIds,
          trailingSectionIds: trailingIds,
          deltaFraction: deltaFraction,
        );
      },
      onResizeEnd: _topologyTransitionController?.previewing == true
          ? null
          : _layoutTransitionController?.commitPreview,
    );
    final effectiveFrame = _topologyTransitionController == null
        ? frame
        : WindowLayoutTopologyScope(
            controller: _topologyTransitionController!,
            child: frame,
          );

    final rail = widget.leadingRail;
    if (widget.railSlots.isEmpty && rail == null) {
      return Scaffold(
        backgroundColor: widget.backgroundColor,
        body: SafeArea(
          child: Padding(
            padding: widget.contentPadding,
            child: effectiveFrame,
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: widget.backgroundColor,
      body: SafeArea(
        child: Row(
          children: [
            Padding(
              padding: widget.railPadding,
              child: rail ??
                  WindowSectionRail(
                    slots: widget.railSlots,
                    onSlotTapped: widget.onRailSlotTapped!,
                    surfaceBuilder: (child) =>
                        _buildRailSurface(context, child),
                  ),
            ),
            Expanded(
              child: Padding(
                padding: widget.contentPadding,
                child: effectiveFrame,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRailSurface(BuildContext context, Widget child) {
    final builder = widget.railSurfaceBuilder;
    if (builder != null) {
      return builder(context, child);
    }
    final theme = Theme.of(context);
    return Material(
      color: theme.colorScheme.surface.withValues(alpha: 0.9),
      elevation: 2,
      borderRadius: BorderRadius.circular(14),
      clipBehavior: Clip.antiAlias,
      child: child,
    );
  }
}
