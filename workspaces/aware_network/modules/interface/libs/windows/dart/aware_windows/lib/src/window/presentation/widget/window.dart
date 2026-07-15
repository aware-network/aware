import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_config.dart';
import '../../domain/model/window_header_data.dart';
import '../../domain/model/window_pane_header.dart';
import '../../domain/provider/window_header_provider.dart';
import '../../domain/presenter/window_pane_presenter.dart';
import '../window_palette.dart';
import '../../domain/provider/window_overlay_provider.dart';
import '../../domain/provider/window_shortcut_provider.dart';
import 'window_divider.dart';
import 'window_header_bar.dart';
import 'window_overlay_host.dart';
import 'window_section.dart';

/// Signature for building the content of a window section.
typedef WindowSectionBuilder =
    Widget Function(
      BuildContext context,
      WidgetRef ref,
      WindowSectionConfig config,
      HeaderControllerArgs headerArgs,
    );

/// Signature for resolving header presentation for a pane type.
typedef WindowPaneHeaderBuilder =
    WindowPaneHeaderData Function(WindowSectionConfig config);

/// Optional resolver that allows hosts to override how a section header renders.
typedef WindowPanePolicyResolver =
    WindowHeaderPolicy? Function(WindowSectionConfig config);

typedef WindowDividerBuilder =
    Widget Function(
      BuildContext context,
      bool isVertical,
      void Function(double delta) onDrag,
      WindowPalette palette,
    );

/// Window container that manages layout based on configuration.
class Window extends ConsumerStatefulWidget {
  const Window({
    super.key,
    required this.config,
    this.sectionBuilder,
    this.headerBuilder,
    this.paletteBuilder,
    this.onSectionResize,
    this.onSectionCollapse,
    this.showSectionHeaders = true,
    this.dividerBuilder,
    this.overlayScrimBuilder,
    this.panePolicyResolver,
    this.showWindowHeader = true,
  });

  final WindowConfig config;
  final WindowSectionBuilder? sectionBuilder;
  final WindowPaneHeaderBuilder? headerBuilder;
  final WindowPalette Function(ThemeData theme)? paletteBuilder;
  final Function(String sectionId, double flex)? onSectionResize;
  final Function(String sectionId)? onSectionCollapse;
  final bool showSectionHeaders;
  final WindowDividerBuilder? dividerBuilder;
  final WindowOverlayScrimBuilder? overlayScrimBuilder;
  final WindowPanePolicyResolver? panePolicyResolver;
  final bool showWindowHeader;

  @override
  ConsumerState<Window> createState() => _WindowState();
}

class _WindowState extends ConsumerState<Window> {
  late WindowConfig _config;
  final Map<String, double> _sectionSizes = {};

  HeaderControllerArgs get _headerArgs => HeaderControllerArgs(
    windowId: _config.id,
    initialData: WindowPaneHeaderData(
      title: _config.name,
      icon: Icons.dashboard_customize,
    ).toHeaderData(),
  );

  @override
  void initState() {
    super.initState();
    _initializeConfig();
  }

  @override
  void didUpdateWidget(Window oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.config != oldWidget.config) {
      _initializeConfig();
    }
  }

  void _initializeConfig() {
    _config = widget.config;
    for (final section in _config.sections) {
      _sectionSizes[section.id] = section.collapsed ? 0.0 : section.flex;
    }

    final headerArgs = _headerArgs;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref
          .read(windowHeaderControllerProvider(headerArgs).notifier)
          .setBase(headerArgs.initialData);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final palette = (widget.paletteBuilder ?? WindowPalette.fromTheme)(theme);
    final headerArgs = _headerArgs;

    final children = <Widget>[];
    if (widget.showWindowHeader) {
      children.add(WindowHeaderBar(headerArgs: headerArgs));
    }
    children.add(
      Expanded(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final layout = _buildLayout(constraints, palette, headerArgs);
            return Stack(
              children: [
                Positioned.fill(child: layout),
                Positioned.fill(
                  child: WindowOverlayHost(
                    headerArgs: headerArgs,
                    scrimBuilder: widget.overlayScrimBuilder,
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );

    return Container(
      color: palette.background,
      child: Column(children: children),
    );
  }

  Widget _buildLayout(
    BoxConstraints constraints,
    WindowPalette palette,
    HeaderControllerArgs headerArgs,
  ) {
    switch (_config.mode) {
      case WindowLayoutMode.horizontal:
        return _buildHorizontalLayout(constraints, palette, headerArgs);
      case WindowLayoutMode.vertical:
        return _buildVerticalLayout(constraints, palette, headerArgs);
      case WindowLayoutMode.grid:
        return _buildGridLayout(constraints, palette, headerArgs);
      case WindowLayoutMode.floating:
        return _buildFloatingLayout(constraints, palette, headerArgs);
    }
  }

  Widget _buildHorizontalLayout(
    BoxConstraints constraints,
    WindowPalette palette,
    HeaderControllerArgs headerArgs,
  ) {
    final List<Widget> children = [];
    final visibleSections = _config.sections
        .where((s) => !s.collapsed)
        .toList();

    for (int i = 0; i < _config.sections.length; i++) {
      final section = _config.sections[i];
      final isLast = i == _config.sections.length - 1;

      if (section.collapsed) {
        children.add(
          _buildCollapsedSection(section, palette, isVertical: false),
        );
      } else {
        final currentFlex = ((_sectionSizes[section.id] ?? section.flex) * 1000)
            .round();
        children.add(
          Expanded(
            flex: currentFlex > 0 ? currentFlex : 1,
            child: WindowSection(
              config: section,
              headerArgs: headerArgs,
              palette: palette,
              showSectionHeader: widget.showSectionHeaders,
              sectionBuilder: _buildSectionContent,
              headerBuilder: _resolveHeader,
              onCollapse: _handleSectionCollapse,
              panePolicyResolver: widget.panePolicyResolver,
            ),
          ),
        );

        if (!isLast) {
          children.add(
            _buildDivider(
              context,
              isVertical: true,
              onDrag: (delta) =>
                  _handleDividerDrag(i, delta, constraints.maxWidth),
              palette: palette,
            ),
          );
        }
      }
    }

    return Row(children: children);
  }

  Widget _buildVerticalLayout(
    BoxConstraints constraints,
    WindowPalette palette,
    HeaderControllerArgs headerArgs,
  ) {
    final List<Widget> children = [];
    final visibleSections = _config.sections
        .where((s) => !s.collapsed)
        .toList();

    for (int i = 0; i < _config.sections.length; i++) {
      final section = _config.sections[i];
      final isLast = i == _config.sections.length - 1;

      if (section.collapsed) {
        children.add(
          _buildCollapsedSection(section, palette, isVertical: true),
        );
      } else {
        final currentFlex = ((_sectionSizes[section.id] ?? section.flex) * 1000)
            .round();
        children.add(
          Expanded(
            flex: currentFlex > 0 ? currentFlex : 1,
            child: WindowSection(
              config: section,
              headerArgs: headerArgs,
              palette: palette,
              showSectionHeader: widget.showSectionHeaders,
              sectionBuilder: _buildSectionContent,
              headerBuilder: _resolveHeader,
              onCollapse: _handleSectionCollapse,
              panePolicyResolver: widget.panePolicyResolver,
            ),
          ),
        );

        if (!isLast) {
          children.add(
            _buildDivider(
              context,
              isVertical: false,
              onDrag: (delta) =>
                  _handleDividerDrag(i, delta, constraints.maxHeight),
              palette: palette,
            ),
          );
        }
      }
    }

    return Column(children: children);
  }

  Widget _buildGridLayout(
    BoxConstraints constraints,
    WindowPalette palette,
    HeaderControllerArgs headerArgs,
  ) {
    final sections = _config.sections.take(4).toList();
    final cellWidth = constraints.maxWidth / 2;
    final cellHeight = constraints.maxHeight / 2;

    Widget buildCell(int index) {
      if (index >= sections.length) return const SizedBox.shrink();
      final section = sections[index];
      return WindowSection(
        config: section,
        headerArgs: headerArgs,
        palette: palette,
        showSectionHeader: widget.showSectionHeaders,
        sectionBuilder: _buildSectionContent,
        headerBuilder: _resolveHeader,
        onCollapse: _handleSectionCollapse,
        panePolicyResolver: widget.panePolicyResolver,
      );
    }

    return Column(
      children: [
        Row(
          children: [
            SizedBox(
              width: cellWidth - 1,
              height: cellHeight - 1,
              child: buildCell(0),
            ),
            Container(width: 2, color: palette.border),
            SizedBox(
              width: cellWidth - 1,
              height: cellHeight - 1,
              child: buildCell(1),
            ),
          ],
        ),
        Container(height: 2, color: palette.border),
        Row(
          children: [
            SizedBox(
              width: cellWidth - 1,
              height: cellHeight - 1,
              child: buildCell(2),
            ),
            Container(width: 2, color: palette.border),
            SizedBox(
              width: cellWidth - 1,
              height: cellHeight - 1,
              child: buildCell(3),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildFloatingLayout(
    BoxConstraints constraints,
    WindowPalette palette,
    HeaderControllerArgs headerArgs,
  ) {
    return Stack(
      children: _config.sections.map((section) {
        final index = _config.sections.indexOf(section);
        return Positioned(
          left: 50.0 * index,
          top: 50.0 * index,
          width: constraints.maxWidth * 0.6,
          height: constraints.maxHeight * 0.6,
          child: Card(
            elevation: 8,
            child: WindowSection(
              config: section,
              headerArgs: headerArgs,
              palette: palette,
              showSectionHeader: widget.showSectionHeaders,
              sectionBuilder: _buildSectionContent,
              headerBuilder: _resolveHeader,
              onCollapse: _handleSectionCollapse,
              panePolicyResolver: widget.panePolicyResolver,
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildSectionContent(
    BuildContext context,
    WidgetRef ref,
    WindowSectionConfig config,
    HeaderControllerArgs headerArgs,
  ) {
    final customBuilder = widget.sectionBuilder;
    if (customBuilder != null) {
      return customBuilder(context, ref, config, headerArgs);
    }

    final presenter = ref
        .read(windowPaneRegistryProvider)
        .presenterFor(config.paneId);
    if (presenter != null) {
      final shortcuts = presenter.buildShortcuts(ref, config, headerArgs);
      if (shortcuts.isNotEmpty) {
        Future.microtask(() {
          if (!mounted) return;
          ref
              .read(windowShortcutRegistryProvider(_config.id).notifier)
              .registerPaneBindings(config.paneId, shortcuts);
        });
      }
      final overlays = presenter.buildOverlays(ref, config, headerArgs);
      if (overlays.isNotEmpty) {
        final overlayRegistry = ref.read(windowOverlayRegistryProvider);
        for (final descriptor in overlays) {
          overlayRegistry.register(descriptor);
        }
      }
      return presenter.build(context, ref, config, headerArgs);
    }

    return Center(child: Text('Pane not registered: ${config.paneId}'));
  }

  WindowPaneHeaderData _resolveHeader(WindowSectionConfig config) {
    final customHeader = widget.headerBuilder?.call(config);
    if (customHeader != null) {
      return customHeader;
    }

    final presenter = ref
        .read(windowPaneRegistryProvider)
        .presenterFor(config.paneId);
    final presenterHeader = presenter?.buildHeader(config);
    if (presenterHeader != null) {
      return presenterHeader;
    }

    return _defaultHeaderBuilder(config);
  }

  Widget _buildDivider(
    BuildContext context, {
    required bool isVertical,
    required void Function(double delta) onDrag,
    required WindowPalette palette,
  }) {
    if (widget.dividerBuilder != null) {
      return widget.dividerBuilder!(context, isVertical, onDrag, palette);
    }

    return WindowDivider(
      isVertical: isVertical,
      onDrag: onDrag,
      borderColor: palette.border,
    );
  }

  Widget _buildCollapsedSection(
    WindowSectionConfig section,
    WindowPalette palette, {
    required bool isVertical,
  }) {
    return Container(
      width: isVertical ? double.infinity : 48,
      height: isVertical ? 48 : double.infinity,
      decoration: BoxDecoration(
        color: palette.card,
        border: Border.all(color: palette.border),
      ),
      child: IconButton(
        icon: Icon(
          isVertical ? Icons.expand_more : Icons.chevron_right,
          color: palette.primary,
        ),
        onPressed: () => _handleSectionCollapse(section.id),
        tooltip: 'Expand ${section.paneId}',
      ),
    );
  }

  void _handleSectionCollapse(String sectionId) {
    final index = _config.sections.indexWhere(
      (section) => section.id == sectionId,
    );
    if (index == -1) return;

    setState(() {
      final section = _config.sections[index];
      final currentSize = _sectionSizes[section.id] ?? section.flex;
      final isCollapsed = currentSize == 0.0;
      _sectionSizes[section.id] = isCollapsed ? section.flex : 0.0;
      _config = _config.copyWith(
        sections: _config.sections
            .map(
              (s) =>
                  s.id == section.id ? s.copyWith(collapsed: !isCollapsed) : s,
            )
            .toList(),
      );
      widget.onSectionCollapse?.call(sectionId);
    });
  }

  void toggleSection(String sectionId) => _handleSectionCollapse(sectionId);

  // Debounce provider updates during resize
  Timer? _updateTimer;
  void _handleDividerDrag(int dividerIndex, double delta, double totalSize) {
    setState(() {
      final leftSection = _config.sections[dividerIndex];
      final rightSection = _config.sections[dividerIndex + 1];

      if (!leftSection.collapsed && !rightSection.collapsed) {
        final leftSize = _sectionSizes[leftSection.id] ?? leftSection.flex;
        final rightSize = _sectionSizes[rightSection.id] ?? rightSection.flex;

        final deltaFlex = delta / totalSize;
        final newLeftSize = (leftSize + deltaFlex).clamp(
          leftSection.minSize,
          leftSection.maxSize,
        );
        final newRightSize = (rightSize - deltaFlex).clamp(
          rightSection.minSize,
          rightSection.maxSize,
        );

        _sectionSizes[leftSection.id] = newLeftSize;
        _sectionSizes[rightSection.id] = newRightSize;

        widget.onSectionResize?.call(leftSection.id, newLeftSize);
        widget.onSectionResize?.call(rightSection.id, newRightSize);

        _updateProviderDebounced();
      }
    });
  }

  void _updateProviderDebounced() {
    _updateTimer?.cancel();
    _updateTimer = Timer(const Duration(milliseconds: 200), () {
      setState(() {});
    });
  }

  @override
  void dispose() {
    _updateTimer?.cancel();
    super.dispose();
  }

  WindowPaneHeaderData _defaultHeaderBuilder(WindowSectionConfig config) {
    final paneId = config.paneId;
    final sanitized = paneId.replaceAll(RegExp(r'[_.-]+'), ' ').trim();
    final title = sanitized.isEmpty
        ? 'Pane'
        : sanitized
              .split(' ')
              .map((part) {
                if (part.isEmpty) return part;
                return part[0].toUpperCase() + part.substring(1);
              })
              .join(' ');
    return WindowPaneHeaderData(title: title);
  }
}

extension on WindowPaneHeaderData {
  WindowHeaderData toHeaderData() => WindowHeaderData(title: title, icon: icon);
}
