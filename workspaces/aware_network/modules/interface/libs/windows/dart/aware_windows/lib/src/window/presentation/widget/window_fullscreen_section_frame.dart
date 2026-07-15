import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../domain/model/window_config.dart';

enum WindowFullscreenSectionRegion { leading, stage, trailing, dock }

typedef WindowFullscreenSectionResizeUpdate =
    void Function(
      Set<String> leadingSectionIds,
      Set<String> trailingSectionIds,
      double deltaFraction,
    );
typedef WindowFullscreenSectionResizeEnd = Future<void> Function();

class WindowFullscreenSectionFrameSection {
  const WindowFullscreenSectionFrameSection({
    required this.id,
    required this.child,
    this.order = 0,
    this.region = WindowFullscreenSectionRegion.stage,
    this.flex = 1.0,
    this.transitionSectionId,
    this.weightMicros,
    this.isVisible = true,
    this.isCollapsed = false,
  });

  final String id;
  final Widget child;
  final int order;
  final WindowFullscreenSectionRegion region;
  final double flex;
  final String? transitionSectionId;
  final int? weightMicros;
  final bool isVisible;
  final bool isCollapsed;

  bool get isActive => isVisible && !isCollapsed;

  WindowFullscreenSectionFrameSection copyWith({
    int? order,
    double? flex,
    int? weightMicros,
    bool? isVisible,
    bool? isCollapsed,
  }) {
    return WindowFullscreenSectionFrameSection(
      id: id,
      child: child,
      order: order ?? this.order,
      region: region,
      flex: flex ?? this.flex,
      transitionSectionId: transitionSectionId,
      weightMicros: weightMicros ?? this.weightMicros,
      isVisible: isVisible ?? this.isVisible,
      isCollapsed: isCollapsed ?? this.isCollapsed,
    );
  }
}

class WindowFullscreenSectionFrame extends StatelessWidget {
  const WindowFullscreenSectionFrame({
    super.key,
    this.header,
    required this.sections,
    this.mode = WindowLayoutMode.grid,
    this.maxContentWidth = 1320,
    this.padding = const EdgeInsets.fromLTRB(28, 24, 28, 32),
    this.sectionSpacing = 18,
    this.columnSpacing = 20,
    this.wideBreakpoint = 1080,
    this.leadingRailWidth = 280,
    this.trailingRailWidth = 360,
    this.dockHeight = 108,
    this.dockSpansLeadingRail = true,
    this.useViewportShellOnWide = true,
    this.onResizeStart,
    this.onResizeUpdate,
    this.onResizeEnd,
  });

  final Widget? header;
  final List<WindowFullscreenSectionFrameSection> sections;
  final WindowLayoutMode mode;
  final double maxContentWidth;
  final EdgeInsets padding;
  final double sectionSpacing;
  final double columnSpacing;
  final double wideBreakpoint;
  final double leadingRailWidth;
  final double trailingRailWidth;
  final double dockHeight;
  final bool dockSpansLeadingRail;
  final bool useViewportShellOnWide;
  final VoidCallback? onResizeStart;
  final WindowFullscreenSectionResizeUpdate? onResizeUpdate;
  final WindowFullscreenSectionResizeEnd? onResizeEnd;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final contentWidth = math.min(maxContentWidth, constraints.maxWidth);
        final orderedSections =
            sections.where((section) => section.isActive).toList()
              ..sort(_compareSections);
        final useWideRegionalLayout =
            contentWidth >= wideBreakpoint && mode != WindowLayoutMode.vertical;
        final canUseViewportShell =
            useViewportShellOnWide &&
            useWideRegionalLayout &&
            constraints.hasBoundedHeight;

        if (canUseViewportShell) {
          final shellHeight = math.max(
            0.0,
            constraints.maxHeight - padding.vertical,
          );
          return Padding(
            padding: padding,
            child: Align(
              alignment: Alignment.topLeft,
              child: SizedBox(
                width: contentWidth,
                height: shellHeight,
                child: _buildViewportShell(
                  orderedSections,
                  contentWidth: contentWidth,
                ),
              ),
            ),
          );
        }

        final body = _buildBody(
          orderedSections,
          contentWidth: contentWidth,
          useWideRegionalLayout: useWideRegionalLayout,
        );

        return SingleChildScrollView(
          padding: padding,
          child: Align(
            alignment: Alignment.topLeft,
            child: SizedBox(width: contentWidth, child: body),
          ),
        );
      },
    );
  }

  Widget _buildBody(
    List<WindowFullscreenSectionFrameSection> orderedSections, {
    required double contentWidth,
    required bool useWideRegionalLayout,
  }) {
    final children = <Widget>[];
    if (header != null) {
      children.add(header!);
    }

    if (orderedSections.isEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: children,
      );
    }

    if (children.isNotEmpty) {
      children.add(SizedBox(height: sectionSpacing));
    }

    if (!useWideRegionalLayout) {
      children.add(_buildSectionColumn(orderedSections));
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: children,
      );
    }

    final leadingSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.leading,
        )
        .toList(growable: false);
    final stageSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.stage,
        )
        .toList(growable: false);
    final trailingSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.trailing,
        )
        .toList(growable: false);
    final dockSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.dock,
        )
        .toList(growable: false);

    if (stageSections.isEmpty) {
      children.add(_buildSectionColumn(orderedSections));
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: children,
      );
    }

    if (dockSections.isNotEmpty &&
        !dockSpansLeadingRail &&
        leadingSections.isNotEmpty) {
      children.add(
        _buildWideShellWithDock(
          leadingSections: leadingSections,
          stageSections: stageSections,
          trailingSections: trailingSections,
          dockSections: dockSections,
          contentWidth: contentWidth,
        ),
      );
    } else {
      children.add(
        _buildWideShellRow(
          leadingSections: leadingSections,
          stageSections: stageSections,
          trailingSections: trailingSections,
          contentWidth: contentWidth,
        ),
      );

      if (dockSections.isNotEmpty) {
        children.add(SizedBox(height: sectionSpacing));
        children.add(_buildSectionColumn(dockSections));
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: children,
    );
  }

  Widget _buildViewportShell(
    List<WindowFullscreenSectionFrameSection> orderedSections, {
    required double contentWidth,
  }) {
    final children = <Widget>[];
    if (header != null) {
      children.add(header!);
    }

    final leadingSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.leading,
        )
        .toList(growable: false);
    final stageSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.stage,
        )
        .toList(growable: false);
    final trailingSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.trailing,
        )
        .toList(growable: false);
    final dockSections = orderedSections
        .where(
          (section) => section.region == WindowFullscreenSectionRegion.dock,
        )
        .toList(growable: false);

    if (stageSections.isEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ...children,
          if (children.isNotEmpty) SizedBox(height: sectionSpacing),
          Expanded(child: _buildScrollableSectionColumn(orderedSections)),
        ],
      );
    }

    if (children.isNotEmpty) {
      children.add(SizedBox(height: sectionSpacing));
    }

    if (dockSections.isNotEmpty &&
        !dockSpansLeadingRail &&
        leadingSections.isNotEmpty) {
      children.add(
        Expanded(
          child: _buildWideShellWithDock(
            leadingSections: leadingSections,
            stageSections: stageSections,
            trailingSections: trailingSections,
            dockSections: dockSections,
            scrollable: true,
            contentWidth: contentWidth,
          ),
        ),
      );
    } else {
      children.add(
        Expanded(
          child: _buildWideShellRow(
            leadingSections: leadingSections,
            stageSections: stageSections,
            trailingSections: trailingSections,
            scrollable: true,
            contentWidth: contentWidth,
          ),
        ),
      );

      if (dockSections.isNotEmpty) {
        children.add(SizedBox(height: sectionSpacing));
        children.add(
          SizedBox(
            height: dockHeight,
            child: _buildScrollableSectionColumn(dockSections),
          ),
        );
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: children,
    );
  }

  Widget _buildWideShellRow({
    required List<WindowFullscreenSectionFrameSection> leadingSections,
    required List<WindowFullscreenSectionFrameSection> stageSections,
    required List<WindowFullscreenSectionFrameSection> trailingSections,
    required double contentWidth,
    bool scrollable = false,
  }) {
    final railChildren = <Widget>[];

    if (leadingSections.isNotEmpty) {
      railChildren.add(
        Flexible(
          flex: _sectionGroupFlex(leadingSections),
          child: scrollable
              ? _buildScrollableSectionColumn(leadingSections)
              : _buildSectionColumn(leadingSections),
        ),
      );
      railChildren.add(
        _buildHorizontalResizeHandle(
          handleKey: 'leading-stage',
          leadingSections: leadingSections,
          trailingSections: [...stageSections, ...trailingSections],
          contentWidth: contentWidth,
        ),
      );
    }

    railChildren.add(
      Flexible(
        flex: _sectionGroupFlex(stageSections),
        child: scrollable
            ? _buildScrollableSectionColumn(stageSections)
            : _buildSectionColumn(stageSections),
      ),
    );

    if (trailingSections.isNotEmpty) {
      railChildren.add(
        _buildHorizontalResizeHandle(
          handleKey: 'stage-trailing',
          leadingSections: stageSections,
          trailingSections: trailingSections,
          contentWidth: contentWidth,
        ),
      );
      railChildren.add(
        Flexible(
          flex: _sectionGroupFlex(trailingSections),
          child: scrollable
              ? _buildScrollableSectionColumn(trailingSections)
              : _buildSectionColumn(trailingSections),
        ),
      );
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: railChildren,
    );
  }

  Widget _buildWideShellWithDock({
    required List<WindowFullscreenSectionFrameSection> leadingSections,
    required List<WindowFullscreenSectionFrameSection> stageSections,
    required List<WindowFullscreenSectionFrameSection> trailingSections,
    required List<WindowFullscreenSectionFrameSection> dockSections,
    required double contentWidth,
    bool scrollable = false,
  }) {
    final workArea = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (scrollable)
          Expanded(
            child: _buildStageTrailingRow(
              stageSections: stageSections,
              trailingSections: trailingSections,
              scrollable: true,
              contentWidth: contentWidth,
            ),
          )
        else
          _buildStageTrailingRow(
            stageSections: stageSections,
            trailingSections: trailingSections,
            contentWidth: contentWidth,
          ),
        SizedBox(height: sectionSpacing),
        if (scrollable)
          SizedBox(
            height: dockHeight,
            child: _buildScrollableSectionColumn(dockSections),
          )
        else
          _buildSectionColumn(dockSections),
      ],
    );

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Flexible(
          flex: _sectionGroupFlex(leadingSections),
          child: scrollable
              ? _buildScrollableSectionColumn(leadingSections)
              : _buildSectionColumn(leadingSections),
        ),
        _buildHorizontalResizeHandle(
          handleKey: 'leading-work-area',
          leadingSections: leadingSections,
          trailingSections: [
            ...stageSections,
            ...trailingSections,
            ...dockSections,
          ],
          contentWidth: contentWidth,
        ),
        Flexible(
          flex: _sectionGroupFlex([...stageSections, ...trailingSections]),
          child: workArea,
        ),
      ],
    );
  }

  Widget _buildStageTrailingRow({
    required List<WindowFullscreenSectionFrameSection> stageSections,
    required List<WindowFullscreenSectionFrameSection> trailingSections,
    required double contentWidth,
    bool scrollable = false,
  }) {
    final railChildren = <Widget>[
      Flexible(
        flex: _sectionGroupFlex(stageSections),
        child: scrollable
            ? _buildScrollableSectionColumn(stageSections)
            : _buildSectionColumn(stageSections),
      ),
    ];

    if (trailingSections.isNotEmpty) {
      railChildren.add(
        _buildHorizontalResizeHandle(
          handleKey: 'stage-trailing',
          leadingSections: stageSections,
          trailingSections: trailingSections,
          contentWidth: contentWidth,
        ),
      );
      railChildren.add(
        Flexible(
          flex: _sectionGroupFlex(trailingSections),
          child: scrollable
              ? _buildScrollableSectionColumn(trailingSections)
              : _buildSectionColumn(trailingSections),
        ),
      );
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: railChildren,
    );
  }

  Widget _buildHorizontalResizeHandle({
    required String handleKey,
    required List<WindowFullscreenSectionFrameSection> leadingSections,
    required List<WindowFullscreenSectionFrameSection> trailingSections,
    required double contentWidth,
  }) {
    final update = onResizeUpdate;
    final leadingIds = _transitionSectionIds(leadingSections);
    final trailingIds = _transitionSectionIds(trailingSections);
    if (update == null || leadingIds.isEmpty || trailingIds.isEmpty) {
      return SizedBox(width: columnSpacing);
    }
    return MouseRegion(
      cursor: SystemMouseCursors.resizeColumn,
      child: GestureDetector(
        key: Key('window-layout-resize-$handleKey'),
        behavior: HitTestBehavior.opaque,
        onHorizontalDragStart: (_) => onResizeStart?.call(),
        onHorizontalDragUpdate: (details) => update(
          leadingIds,
          trailingIds,
          details.delta.dx / math.max(1.0, contentWidth),
        ),
        onHorizontalDragEnd: (_) => onResizeEnd?.call(),
        child: SizedBox(width: columnSpacing),
      ),
    );
  }

  Widget _buildSectionColumn(
    List<WindowFullscreenSectionFrameSection> sections,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: _withSpacing(
        sections
            .map(
              (section) => KeyedSubtree(
                key: Key('window-fullscreen-section-${section.id}'),
                child: section.child,
              ),
            )
            .toList(growable: false),
        sectionSpacing,
      ),
    );
  }

  Widget _buildScrollableSectionColumn(
    List<WindowFullscreenSectionFrameSection> sections,
  ) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (!constraints.hasBoundedHeight) {
          return SingleChildScrollView(child: _buildSectionColumn(sections));
        }
        return SingleChildScrollView(
          child: SizedBox(
            height: constraints.maxHeight,
            child: _buildFlexibleSectionColumn(sections),
          ),
        );
      },
    );
  }

  Widget _buildFlexibleSectionColumn(
    List<WindowFullscreenSectionFrameSection> sections,
  ) {
    if (sections.isEmpty) {
      return const SizedBox.shrink();
    }
    final children = <Widget>[];
    for (var index = 0; index < sections.length; index += 1) {
      if (index > 0) {
        children.add(SizedBox(height: sectionSpacing));
      }
      final section = sections[index];
      children.add(
        Expanded(
          flex: _sectionFlex(section),
          child: KeyedSubtree(
            key: Key('window-fullscreen-section-${section.id}'),
            child: section.child,
          ),
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: children,
    );
  }

  List<Widget> _withSpacing(List<Widget> children, double spacing) {
    if (children.isEmpty) {
      return const <Widget>[];
    }
    final widgets = <Widget>[];
    for (var index = 0; index < children.length; index += 1) {
      if (index > 0) {
        widgets.add(SizedBox(height: spacing));
      }
      widgets.add(children[index]);
    }
    return widgets;
  }
}

Set<String> _transitionSectionIds(
  List<WindowFullscreenSectionFrameSection> sections,
) {
  return {
    for (final section in sections)
      if ((section.transitionSectionId ?? '').trim().isNotEmpty)
        section.transitionSectionId!.trim(),
  };
}

int _compareSections(
  WindowFullscreenSectionFrameSection a,
  WindowFullscreenSectionFrameSection b,
) {
  final byOrder = a.order.compareTo(b.order);
  if (byOrder != 0) {
    return byOrder;
  }
  return a.id.compareTo(b.id);
}

int _sectionGroupFlex(List<WindowFullscreenSectionFrameSection> sections) {
  final total = sections.fold<double>(
    0.0,
    (sum, section) =>
        sum + (section.flex.isFinite && section.flex > 0 ? section.flex : 1.0),
  );
  return math.max(1, (total * 1000).round());
}

int _sectionFlex(WindowFullscreenSectionFrameSection section) {
  return math.max(
    1,
    ((section.flex.isFinite && section.flex > 0 ? section.flex : 1.0) * 1000)
        .round(),
  );
}
