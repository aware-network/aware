import 'dart:async';

import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_interface_sdk/aware_interface_sdk.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/pane_api_scope.dart';
import 'pane_render_spec.dart';
import 'render_component_registry.dart';

const String _capabilityKindNodeKind = 'node_kind';
const String _capabilityKindLayoutKind = 'layout_kind';
const String _capabilityKindInputKind = 'input_kind';
const String _capabilityKindActionBinding = 'action_binding';
const String _capabilityKindReceipt = 'receipt';
const String _capabilityKindRenderComponent =
    kPaneRenderCapabilityKindRenderComponent;
const String _layoutCompactRow = 'compact_row';
const String _layoutComposer = 'composer';
const String _layoutMessageBubble = 'message_bubble';
const String _layoutMessageThread = 'message_thread';
const String _layoutMetadataBar = 'metadata_bar';
const String _layoutPaneHeader = 'pane_header';
const String _layoutSummaryBar = 'summary_bar';
const String _typographyPaneTitle = 'pane_title';
const Set<String> _storageMediaImageComponentRefs = <String>{
  'aware.storage.media',
  'aware.storage.media.image',
  'storage.media',
  'storage.media.image',
};

const Set<String> _supportedNodeKinds = <String>{
  kPaneRenderNodeKindBox,
  kPaneRenderNodeKindColumn,
  kPaneRenderNodeKindDisclosure,
  kPaneRenderNodeKindField,
  kPaneRenderNodeKindListItem,
  kPaneRenderNodeKindMetric,
  kPaneRenderNodeKindRow,
  kPaneRenderNodeKindScroll,
  kPaneRenderNodeKindSectionHeader,
  kPaneRenderNodeKindRepeat,
  kPaneRenderNodeKindText,
  kPaneRenderNodeKindStatus,
  kPaneRenderNodeKindTextInput,
  kPaneRenderNodeKindButton,
  kPaneRenderNodeKindReceipt,
  kPaneRenderNodeKindComponent,
};

const Set<String> _supportedLayoutKinds = <String>{
  _layoutCompactRow,
  _layoutComposer,
  _layoutMessageBubble,
  _layoutMessageThread,
  _layoutMetadataBar,
  _layoutPaneHeader,
  _layoutSummaryBar,
};

const Set<String> _supportedInputKinds = <String>{kPaneRenderNodeKindTextInput};

const Set<String> _supportedActionBindingKinds = <String>{
  kPaneRenderActionKindAction,
  kPaneRenderActionKindApiEndpoint,
  kPaneRenderActionKindSdkOperation,
  kPaneRenderActionKindViewAction,
};

const Set<String> _supportedStateTransforms = <String>{
  kPaneRenderStateTransformRaw,
  kPaneRenderStateTransformText,
  kPaneRenderStateTransformCount,
  kPaneRenderStateTransformExists,
  kPaneRenderStateTransformPluralCount,
  kPaneRenderStateTransformNotEmpty,
  kPaneRenderStateTransformIsEmpty,
};

class PaneRenderSpecWidget extends StatefulWidget {
  const PaneRenderSpecWidget({
    required this.spec,
    required this.paneContext,
    super.key,
    this.materializedState,
    this.onInvokeAction,
    this.mediaResolver,
    this.renderComponentRegistry = const RenderComponentRegistry.empty(),
    this.onBuild,
  });

  final PaneRenderSpec spec;
  final PaneContext paneContext;
  final InterfaceMaterializedPaneState? materializedState;
  final PaneRenderActionInvoker? onInvokeAction;
  final InterfaceStorageMediaResolver? mediaResolver;
  final RenderComponentRegistry renderComponentRegistry;
  final ValueChanged<String>? onBuild;

  @override
  State<PaneRenderSpecWidget> createState() => _PaneRenderSpecWidgetState();
}

class _PaneRenderSpecWidgetState extends State<PaneRenderSpecWidget> {
  final Map<String, _PaneRenderTextInputState> _textInputs =
      <String, _PaneRenderTextInputState>{};
  final Set<String> _pendingActionKeys = <String>{};
  final Map<String, String> _actionErrors = <String, String>{};
  final Map<String, StorageMediaResolution> _resolvedMedia =
      <String, StorageMediaResolution>{};
  final Set<String> _pendingMediaKeys = <String>{};
  int _mediaResolutionEpoch = 0;

  @override
  void dispose() {
    for (final input in _textInputs.values) {
      input.dispose();
    }
    super.dispose();
  }

  @override
  void didUpdateWidget(PaneRenderSpecWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.materializedState != widget.materializedState ||
        oldWidget.spec != widget.spec) {
      _syncControllersFromState();
    }
    if (oldWidget.materializedState != widget.materializedState ||
        oldWidget.spec != widget.spec ||
        oldWidget.mediaResolver != widget.mediaResolver) {
      _resetMediaResolutionState();
    }
  }

  @override
  Widget build(BuildContext context) {
    widget.onBuild?.call('PaneRenderSpecWidget:${widget.spec.paneKind}');
    final unsupportedCapabilities = _unsupportedCapabilities();
    if (unsupportedCapabilities.isNotEmpty) {
      return _buildUnsupportedSpec(context, unsupportedCapabilities);
    }
    final roots = widget.spec.childrenOf(null);
    final scope = _PaneRenderStateScope(
      materializedState: widget.materializedState,
    );
    if (roots.isEmpty) {
      return const SizedBox.shrink();
    }
    if (roots.length == 1) {
      return _buildNode(context, roots.single, scope);
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: _withSpacing(
        roots
            .map((node) => _buildNode(context, node, scope))
            .toList(growable: false),
      ),
    );
  }

  Widget _buildNode(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    if (!_visible(node, scope)) {
      return const SizedBox.shrink();
    }
    return switch (node.nodeKind) {
      kPaneRenderNodeKindBox => _buildBox(context, node, scope),
      kPaneRenderNodeKindColumn => _buildColumn(context, node, scope),
      kPaneRenderNodeKindDisclosure => _buildDisclosure(context, node, scope),
      kPaneRenderNodeKindField => _buildField(context, node, scope),
      kPaneRenderNodeKindListItem => _buildListItem(context, node, scope),
      kPaneRenderNodeKindMetric => _buildMetric(context, node, scope),
      kPaneRenderNodeKindRow => _buildRow(context, node, scope),
      kPaneRenderNodeKindScroll => _buildScroll(context, node, scope),
      kPaneRenderNodeKindSectionHeader => _buildSectionHeader(
          context,
          node,
          scope,
        ),
      kPaneRenderNodeKindRepeat => _buildRepeat(context, node, scope),
      kPaneRenderNodeKindText => _buildText(context, node, scope),
      kPaneRenderNodeKindStatus => _buildStatus(context, node, scope),
      kPaneRenderNodeKindTextInput => _buildTextInput(context, node, scope),
      kPaneRenderNodeKindButton => _buildButton(context, node, scope),
      kPaneRenderNodeKindReceipt => _buildReceipt(context, node, scope),
      kPaneRenderNodeKindComponent => _buildRenderComponentFallback(
          context,
          node,
          scope,
        ),
      _ => _buildUnsupportedNode(context, node),
    };
  }

  Widget _buildBox(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: _buildColumn(context, node, scope),
      ),
    );
  }

  Widget _buildColumn(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    return Column(
      crossAxisAlignment: _columnCrossAxisAlignment(node),
      mainAxisSize: MainAxisSize.min,
      children: _withSpacing(_buildChildren(context, node, scope)),
    );
  }

  CrossAxisAlignment _columnCrossAxisAlignment(PaneRenderNode node) {
    final layout = _styleToken(node, 'layout');
    final align = _styleToken(node, 'align');
    if (layout == _layoutPaneHeader || align == 'center') {
      return CrossAxisAlignment.center;
    }
    if (align == 'end') {
      return CrossAxisAlignment.end;
    }
    return CrossAxisAlignment.stretch;
  }

  Widget _buildField(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final label = node.label?.trim();
    final value = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        '';
    final children = _buildChildren(context, node, scope);
    final content = <Widget>[
      if (label != null && label.isNotEmpty)
        Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
            fontWeight: FontWeight.w700,
          ),
        ),
      if (value.trim().isNotEmpty)
        Text(
          value,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface,
          ),
        ),
      ...children,
    ];
    if (content.isEmpty) {
      return const SizedBox.shrink();
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: _withSpacing(content),
    );
  }

  Widget _buildMetric(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final value = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        '0';
    final label = node.label?.trim();
    if (value.trim().isEmpty && (label == null || label.isEmpty)) {
      return const SizedBox.shrink();
    }
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withAlpha(120),
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Text(
              value,
              style: theme.textTheme.titleSmall?.copyWith(
                color: theme.colorScheme.onSurface,
                fontWeight: FontWeight.w800,
              ),
            ),
            if (label != null && label.isNotEmpty)
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildCompactMetric(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final value = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        '0';
    final label = node.label?.trim();
    if (value.trim().isEmpty && (label == null || label.isEmpty)) {
      return const SizedBox.shrink();
    }
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withAlpha(90),
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: <Widget>[
            Text(
              value,
              style: theme.textTheme.labelLarge?.copyWith(
                color: theme.colorScheme.onSurface,
                fontWeight: FontWeight.w800,
              ),
            ),
            if (label != null && label.isNotEmpty) ...<Widget>[
              const SizedBox(width: 5),
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildListItem(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final children = _buildChildren(context, node, scope);
    final text = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        node.label;
    if (children.isEmpty && (text == null || text.trim().isEmpty)) {
      return const SizedBox.shrink();
    }
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withAlpha(180),
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: _withSpacing(<Widget>[
            if (text != null && text.trim().isNotEmpty)
              Text(
                text,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ...children,
          ]),
        ),
      ),
    );
  }

  Widget _buildDisclosure(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final children = widget.spec.childrenOf(node.nodeKey);
    final summaryNodes =
        children.where((child) => child.slotKey == 'summary').toList();
    final detailNodes = children
        .where((child) => child.slotKey != 'summary')
        .toList(growable: false);
    final summaryWidgets = summaryNodes
        .map((child) => _buildNode(context, child, scope))
        .toList(growable: false);
    final detailWidgets = detailNodes
        .map((child) => _buildNode(context, child, scope))
        .toList(growable: false);
    final titleText = _stringProperty(node, 'identity', scope) ??
        node.text ??
        node.label ??
        'Details';
    final initiallyExpanded = scope.itemIndex == null || scope.itemIndex == 0;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withAlpha(150),
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Material(
          type: MaterialType.transparency,
          child: ExpansionTile(
            initiallyExpanded: initiallyExpanded,
            tilePadding: const EdgeInsets.symmetric(horizontal: 12),
            childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
            title: summaryWidgets.isEmpty
                ? Text(
                    titleText,
                    style: theme.textTheme.titleSmall?.copyWith(
                      color: theme.colorScheme.onSurface,
                      fontWeight: FontWeight.w800,
                    ),
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    mainAxisSize: MainAxisSize.min,
                    children: _withSpacing(summaryWidgets),
                  ),
            children: _withSpacing(detailWidgets),
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final text = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        node.label ??
        '';
    if (text.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    return Padding(
      padding: const EdgeInsets.only(top: 4, bottom: 2),
      child: Text(
        text,
        style: theme.textTheme.labelLarge?.copyWith(
          color: theme.colorScheme.onSurface,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }

  Widget _buildRow(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    if (_styleToken(node, 'layout') == _layoutMetadataBar) {
      return Wrap(
        spacing: 8,
        runSpacing: 8,
        alignment: _wrapAlignment(node),
        crossAxisAlignment: WrapCrossAlignment.center,
        children: widget.spec
            .childrenOf(node.nodeKey)
            .map((child) => _buildMetadataBarChild(context, child, scope))
            .toList(growable: false),
      );
    }
    if (_styleToken(node, 'layout') == _layoutSummaryBar) {
      return _buildSummaryBar(context, node, scope);
    }
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      alignment: _wrapAlignment(node),
      crossAxisAlignment: WrapCrossAlignment.center,
      children: _buildChildren(context, node, scope),
    );
  }

  Widget _buildSummaryBar(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final children = widget.spec.childrenOf(node.nodeKey);
    if (children.isEmpty) {
      return const SizedBox.shrink();
    }
    final rowChildren = <Widget>[];
    for (var index = 0; index < children.length; index++) {
      final child = _buildSummaryBarChild(context, children[index], scope);
      if (index == 0) {
        rowChildren.add(Expanded(child: child));
      } else {
        rowChildren.add(const SizedBox(width: 10));
        rowChildren.add(child);
      }
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: rowChildren,
    );
  }

  Widget _buildSummaryBarChild(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    if (!_visible(node, scope)) {
      return const SizedBox.shrink();
    }
    if (node.nodeKind == kPaneRenderNodeKindStatus) {
      return _buildStatusBadge(context, node, scope);
    }
    if (node.nodeKind == kPaneRenderNodeKindMetric) {
      return _buildCompactMetric(context, node, scope);
    }
    return _buildNode(context, node, scope);
  }

  WrapAlignment _wrapAlignment(PaneRenderNode node) {
    final align = _styleToken(node, 'align');
    if (align == 'center') {
      return WrapAlignment.center;
    }
    if (align == 'end') {
      return WrapAlignment.end;
    }
    return WrapAlignment.start;
  }

  Widget _buildMetadataBarChild(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    if (!_visible(node, scope)) {
      return const SizedBox.shrink();
    }
    if (node.nodeKind == kPaneRenderNodeKindMetric) {
      return _buildCompactMetric(context, node, scope);
    }
    if (node.nodeKind == kPaneRenderNodeKindStatus) {
      return _buildStatusBadge(context, node, scope);
    }
    return _buildNode(context, node, scope);
  }

  Widget _buildScroll(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    return SingleChildScrollView(child: _buildColumn(context, node, scope));
  }

  Widget _buildRepeat(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final items = _items(node, scope);
    if (items.isEmpty) {
      return const SizedBox.shrink();
    }
    final children = <Widget>[];
    for (var index = 0; index < items.length; index++) {
      final item = items[index];
      final itemScope = scope.withItem(item, index);
      children.addAll(_buildChildren(context, node, itemScope));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: _withSpacing(children),
    );
  }

  Widget _buildText(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final text = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        node.label ??
        '';
    if (text.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    final isHeading = node.semanticRole == 'heading';
    final emphasis = _styleToken(node, 'emphasis');
    final tone = _styleToken(node, 'tone');
    final typography = _styleToken(node, 'typography');
    var style =
        isHeading ? theme.textTheme.titleMedium : theme.textTheme.bodyMedium;
    if (typography == _typographyPaneTitle) {
      style = theme.textTheme.headlineSmall?.copyWith(
        color: theme.colorScheme.onSurface,
        fontWeight: FontWeight.w800,
        height: 1.05,
      );
    }
    if (emphasis == 'primary') {
      style = style?.copyWith(
        color: theme.colorScheme.onSurface,
        fontWeight: FontWeight.w700,
      );
    } else if (tone == 'muted' || tone == 'provenance') {
      style = style?.copyWith(color: theme.colorScheme.onSurfaceVariant);
    }
    final shouldTruncate = _styleToken(node, 'overflow') == 'truncate';
    return Text(
      text,
      style: style,
      textAlign: _textAlign(node),
      maxLines: shouldTruncate ? 1 : null,
      overflow: shouldTruncate ? TextOverflow.ellipsis : null,
      softWrap: !shouldTruncate,
    );
  }

  TextAlign? _textAlign(PaneRenderNode node) {
    final align = _styleToken(node, 'align');
    if (align == 'center') {
      return TextAlign.center;
    }
    if (align == 'end') {
      return TextAlign.end;
    }
    return null;
  }

  Widget _buildStatus(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    return Align(
      alignment: Alignment.centerLeft,
      child: _buildStatusBadge(context, node, scope),
    );
  }

  Widget _buildStatusBadge(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final text = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        node.label ??
        '';
    if (text.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    final colors = _toneColors(
      theme,
      _stringProperty(node, kPaneRenderStateTargetTone, scope) ??
          _styleToken(node, 'tone'),
    );
    return Semantics(
      liveRegion: true,
      label: 'Status $text',
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: colors.background,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: colors.outline),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Text(
            text,
            style: theme.textTheme.labelMedium?.copyWith(
              color: colors.foreground,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextInput(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final controller = _controllerFor(node, scope);
    final isMultiline = _styleToken(node, 'input') == 'multiline' ||
        _styleToken(node, 'multiline') == 'true';
    return TextField(
      controller: controller,
      enabled: _enabled(node, scope),
      keyboardType: isMultiline ? TextInputType.multiline : TextInputType.text,
      minLines: isMultiline ? 3 : 1,
      maxLines: isMultiline ? 6 : 1,
      decoration: InputDecoration(
        labelText: node.label,
        hintText: node.placeholder,
        border: const OutlineInputBorder(),
        filled: true,
        fillColor: theme.colorScheme.surface.withAlpha(160),
        isDense: true,
      ),
    );
  }

  Widget _buildButton(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final action = _actionFor(node, kPaneRenderActionEventActivate);
    final label = action?.label ?? node.label ?? node.text ?? action?.actionKey;
    final actionInvocationKey =
        action == null ? null : _actionInvocationKey(action, scope);
    final pending = action != null &&
        actionInvocationKey != null &&
        _pendingActionKeys.contains(actionInvocationKey);
    final error =
        actionInvocationKey == null ? null : _actionErrors[actionInvocationKey];
    final button = Align(
      alignment: Alignment.centerLeft,
      child: ElevatedButton(
        style: _buttonStyle(context, node),
        onPressed: action == null || pending || !_enabled(node, scope)
            ? null
            : () => _invoke(action, scope),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            if (pending) ...<Widget>[
              const SizedBox.square(
                dimension: 14,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              const SizedBox(width: 8),
            ],
            Text(label ?? 'Action'),
          ],
        ),
      ),
    );
    if (error == null) {
      return button;
    }
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        button,
        const SizedBox(height: 6),
        Text(
          error,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.error,
          ),
        ),
      ],
    );
  }

  Widget _buildReceipt(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final text = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.text ??
        node.label;
    if (text == null || text.trim().isEmpty) {
      return const SizedBox.shrink();
    }
    final theme = Theme.of(context);
    return Semantics(
      liveRegion: true,
      label: 'Receipt $text',
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: theme.colorScheme.surface.withAlpha(190),
          border: Border.all(color: theme.colorScheme.outlineVariant),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Icon(
                Icons.check_circle_outline,
                size: 16,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  text,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRenderComponentFallback(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    if (_isStorageMediaImageComponent(node)) {
      return _buildStorageMediaImage(context, node, scope);
    }

    final native = widget.renderComponentRegistry.build(
      context,
      _componentBuildDataFor(node, scope),
    );
    if (native != null) {
      return native;
    }

    final fallbackKind = node.fallbackNodeKind;
    if (fallbackKind != null &&
        fallbackKind != kPaneRenderNodeKindComponent &&
        _supportedNodeKinds.contains(fallbackKind)) {
      return _buildNode(context, node.withNodeKind(fallbackKind), scope);
    }

    final theme = Theme.of(context);
    final componentRef = node.componentRef?.trim();
    final headline = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.fallbackText ??
        node.text ??
        node.label ??
        'Render component unavailable';
    final details = componentRef == null || componentRef.isEmpty
        ? 'Missing component_ref'
        : componentRef;
    final children = _buildChildren(context, node, scope);

    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withAlpha(110),
        border: Border.all(color: theme.colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: _withSpacing(<Widget>[
            Text(
              headline,
              style: theme.textTheme.titleSmall?.copyWith(
                color: theme.colorScheme.onSurface,
                fontWeight: FontWeight.w800,
              ),
            ),
            Text(
              details,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            ...children,
          ]),
        ),
      ),
    );
  }

  bool _isStorageMediaImageComponent(PaneRenderNode node) {
    final componentRef = node.componentRef?.trim();
    if (componentRef == null || componentRef.isEmpty) {
      return false;
    }
    return _storageMediaImageComponentRefs.contains(componentRef);
  }

  Widget _buildStorageMediaImage(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final theme = Theme.of(context);
    final media = _mediaProperty(node, scope);
    final resolution = _mediaResolutionFromValue(media);
    final source = _renderableMediaSource(resolution);
    final label = _stringProperty(node, kPaneRenderStateTargetText, scope) ??
        node.label ??
        resolution?.filename ??
        resolution?.mediaRef.filename ??
        'Storage media';
    final aspectRatio = _positiveDouble(_styleToken(node, 'aspect_ratio')) ??
        _positiveDouble(_styleToken(node, 'aspectRatio')) ??
        (16 / 9);
    final imageRadius = BorderRadius.circular(8);

    if (source == null) {
      final isPending = _mediaPending(node, scope);
      return Semantics(
        label: label,
        image: true,
        child: AspectRatio(
          aspectRatio: aspectRatio,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withAlpha(120),
              border: Border.all(color: theme.colorScheme.outlineVariant),
              borderRadius: imageRadius,
            ),
            child: Center(
              child: isPending
                  ? const SizedBox.square(
                      dimension: 22,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(
                      Icons.image_not_supported_outlined,
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
            ),
          ),
        ),
      );
    }

    return Semantics(
      label: label,
      image: true,
      child: ClipRRect(
        borderRadius: imageRadius,
        child: AspectRatio(
          aspectRatio: aspectRatio,
          child: Image.network(
            source,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) {
              return DecoratedBox(
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest.withAlpha(
                    120,
                  ),
                  border: Border.all(color: theme.colorScheme.outlineVariant),
                ),
                child: Center(
                  child: Icon(
                    Icons.broken_image_outlined,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildUnsupportedSpec(
    BuildContext context,
    List<_UnsupportedPaneRenderCapability> capabilities,
  ) {
    final theme = Theme.of(context);
    final missing = capabilities.map((item) => item.label).join(', ');
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer.withAlpha(120),
        border: Border.all(color: theme.colorScheme.error.withAlpha(140)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Text(
              'Pane renderer missing required capability',
              style: theme.textTheme.titleSmall?.copyWith(
                color: theme.colorScheme.onErrorContainer,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              missing,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onErrorContainer,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildUnsupportedNode(BuildContext context, PaneRenderNode node) {
    final theme = Theme.of(context);
    return Text(
      'Unsupported pane node kind: ${node.nodeKind}',
      style: theme.textTheme.bodySmall?.copyWith(
        color: theme.colorScheme.error,
      ),
    );
  }

  List<_UnsupportedPaneRenderCapability> _unsupportedCapabilities() {
    final unsupported = <_UnsupportedPaneRenderCapability>[];
    for (final requirement in widget.spec.rendererRequirements) {
      if (!requirement.isRequired) {
        continue;
      }
      if (!_supportsRequirement(requirement)) {
        unsupported.add(
          _UnsupportedPaneRenderCapability(
            kind: requirement.capabilityKind,
            key: requirement.capabilityKey,
          ),
        );
      }
    }
    for (final node in widget.spec.nodes) {
      if (!_supportedNodeKinds.contains(node.nodeKind)) {
        unsupported.add(
          _UnsupportedPaneRenderCapability(
            kind: _capabilityKindNodeKind,
            key: node.nodeKind,
          ),
        );
      }
      for (final binding in node.stateBindings) {
        if (!_supportedStateTransforms.contains(binding.transform)) {
          unsupported.add(
            _UnsupportedPaneRenderCapability(
              kind: 'state_transform',
              key: binding.transform,
            ),
          );
        }
      }
    }
    return _deduplicateCapabilities(unsupported);
  }

  bool _supportsRequirement(PaneRendererCapabilityRequirement requirement) {
    final key = requirement.capabilityKey;
    final kind = requirement.capabilityKind;
    if (kind == _capabilityKindNodeKind) {
      return _supportedNodeKinds.contains(key);
    }
    if (kind == _capabilityKindLayoutKind) {
      return _supportedLayoutKinds.contains(key);
    }
    if (kind == _capabilityKindInputKind) {
      return _supportedInputKinds.contains(key);
    }
    if (kind == _capabilityKindActionBinding) {
      return _supportedActionBindingKinds.contains(key);
    }
    if (kind == _capabilityKindReceipt) {
      return key == kPaneRenderNodeKindReceipt;
    }
    if (kind == _capabilityKindRenderComponent) {
      return widget.renderComponentRegistry.supports(key);
    }
    return false;
  }

  List<Widget> _buildChildren(
    BuildContext context,
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    return widget.spec
        .childrenOf(node.nodeKey)
        .map((child) => _buildNode(context, child, scope))
        .toList(growable: false);
  }

  List<Widget> _withSpacing(List<Widget> children) {
    if (children.length < 2) {
      return children;
    }
    return <Widget>[
      for (var index = 0; index < children.length; index++) ...[
        children[index],
        if (index < children.length - 1) const SizedBox(height: 8),
      ],
    ];
  }

  TextEditingController _controllerFor(
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final canonicalValue = _stringProperty(
          node,
          kPaneRenderStateTargetValue,
          scope,
          includeDraft: false,
        ) ??
        '';
    final existing = _textInputs[node.nodeKey];
    if (existing != null) {
      existing.syncFromCanonical(canonicalValue);
      return existing.controller;
    }
    final input = _PaneRenderTextInputState(
      canonicalValue: canonicalValue,
      onDraftChanged: () {
        if (mounted) {
          setState(() {});
        }
      },
    );
    _textInputs[node.nodeKey] = input;
    return input.controller;
  }

  void _syncControllersFromState() {
    final scope = _PaneRenderStateScope(
      materializedState: widget.materializedState,
    );
    for (final entry in _textInputs.entries) {
      final node = _nodeForKey(entry.key);
      if (node == null) {
        continue;
      }
      final next = _stringProperty(
            node,
            kPaneRenderStateTargetValue,
            scope,
            includeDraft: false,
          ) ??
          '';
      entry.value.syncFromCanonical(next);
    }
  }

  PaneRenderNode? _nodeForKey(String nodeKey) {
    for (final node in widget.spec.nodes) {
      if (node.nodeKey == nodeKey) {
        return node;
      }
    }
    return null;
  }

  bool _visible(PaneRenderNode node, _PaneRenderStateScope scope) {
    final value = _property(node, kPaneRenderStateTargetVisible, scope);
    if (value is bool) {
      return value;
    }
    if (value is String) {
      return value.trim().toLowerCase() != 'false';
    }
    return true;
  }

  bool _enabled(PaneRenderNode node, _PaneRenderStateScope scope) {
    final value = _property(node, kPaneRenderStateTargetEnabled, scope);
    if (value is bool) {
      return value;
    }
    if (value is String) {
      return value.trim().toLowerCase() != 'false';
    }
    return true;
  }

  String? _stringProperty(
    PaneRenderNode node,
    String targetProperty,
    _PaneRenderStateScope scope, {
    bool includeDraft = true,
  }) {
    final value = _property(
      node,
      targetProperty,
      scope,
      includeDraft: includeDraft,
    );
    if (value == null) {
      return null;
    }
    final text = value.toString().trim();
    return text.isEmpty ? null : text;
  }

  Object? _property(
    PaneRenderNode node,
    String targetProperty,
    _PaneRenderStateScope scope, {
    bool includeDraft = true,
  }) {
    for (final binding in node.stateBindings) {
      if (binding.targetProperty != targetProperty) {
        continue;
      }
      final raw = includeDraft
          ? _resolveBindingRaw(binding, scope)
          : _resolveMaterializedBindingRaw(binding, scope);
      final value = paneRenderApplyStateTransform(binding, raw);
      if (targetProperty == kPaneRenderStateTargetMediaRef) {
        return _mediaBindingValue(binding, scope, raw, value);
      }
      return value;
    }
    return null;
  }

  Object? _mediaProperty(PaneRenderNode node, _PaneRenderStateScope scope) {
    final bound = _property(node, kPaneRenderStateTargetMediaRef, scope);
    if (bound != null) {
      return bound;
    }
    final inputs = _componentInputsFor(node, scope);
    return inputs['media_ref'] ?? inputs['media'] ?? inputs['image'];
  }

  Object? _mediaBindingValue(
    PaneStateBinding binding,
    _PaneRenderStateScope scope,
    Object? raw,
    Object? value,
  ) {
    final resolved =
        _mediaResolutionFromValue(value) ?? _mediaResolutionFromValue(raw);
    if (resolved != null) {
      return resolved;
    }
    final mediaRef = _mediaRefFromValue(value) ?? _mediaRefFromValue(raw);
    if (mediaRef == null) {
      return value;
    }
    final key = _mediaResolutionKey(binding, scope, mediaRef);
    final cached = _resolvedMedia[key];
    if (cached != null) {
      return cached;
    }
    _ensureMediaResolution(key: key, mediaRef: mediaRef);
    return mediaRef;
  }

  void _ensureMediaResolution({
    required String key,
    required StorageMediaRef mediaRef,
  }) {
    final resolver = widget.mediaResolver;
    if (resolver == null ||
        _resolvedMedia.containsKey(key) ||
        _pendingMediaKeys.contains(key)) {
      return;
    }
    _pendingMediaKeys.add(key);
    final epoch = _mediaResolutionEpoch;
    unawaited(
      resolver.resolveMediaRef(mediaRef: mediaRef).then((resolution) {
        if (!mounted || epoch != _mediaResolutionEpoch) {
          return;
        }
        setState(() {
          _resolvedMedia[key] = resolution;
          _pendingMediaKeys.remove(key);
        });
      }).catchError((Object error) {
        if (!mounted || epoch != _mediaResolutionEpoch) {
          return;
        }
        setState(() {
          _pendingMediaKeys.remove(key);
        });
      }),
    );
  }

  bool _mediaPending(PaneRenderNode node, _PaneRenderStateScope scope) {
    for (final binding in node.stateBindings) {
      if (binding.targetProperty != kPaneRenderStateTargetMediaRef) {
        continue;
      }
      final raw = _resolveBindingRaw(binding, scope);
      final mediaRef = _mediaRefFromValue(raw);
      if (mediaRef == null) {
        continue;
      }
      final key = _mediaResolutionKey(binding, scope, mediaRef);
      if (_pendingMediaKeys.contains(key)) {
        return true;
      }
    }
    return false;
  }

  void _resetMediaResolutionState() {
    _mediaResolutionEpoch += 1;
    _resolvedMedia.clear();
    _pendingMediaKeys.clear();
  }

  Object? _resolveBindingRaw(
    PaneStateBinding binding,
    _PaneRenderStateScope scope,
  ) {
    final draftValue = _draftValueFor(binding, scope);
    if (draftValue != null) {
      return draftValue;
    }
    return paneRenderResolveStatePath(
      scope.materializedState,
      binding.jsonPath,
      item: scope.item,
      parentItem: scope.parentItem,
      itemIndex: scope.itemIndex,
      parentIndex: scope.parentIndex,
    );
  }

  Object? _draftValueFor(
    PaneStateBinding binding,
    _PaneRenderStateScope scope,
  ) {
    if (scope.item != null || scope.parentItem != null) {
      return null;
    }
    final jsonPath = _trimmedOrNull(binding.jsonPath);
    if (jsonPath == null) {
      return null;
    }
    for (final node in widget.spec.nodes) {
      if (node.nodeKind != kPaneRenderNodeKindTextInput) {
        continue;
      }
      final input = _textInputs[node.nodeKey];
      if (input == null || !input.hasLocalEdit) {
        continue;
      }
      for (final inputBinding in node.stateBindings) {
        if (inputBinding.targetProperty != kPaneRenderStateTargetValue) {
          continue;
        }
        if (_trimmedOrNull(inputBinding.jsonPath) == jsonPath) {
          return input.controller.text;
        }
      }
    }
    return null;
  }

  Object? _resolveMaterializedBindingRaw(
    PaneStateBinding binding,
    _PaneRenderStateScope scope,
  ) {
    return paneRenderResolveStatePath(
      scope.materializedState,
      binding.jsonPath,
      item: scope.item,
      parentItem: scope.parentItem,
      itemIndex: scope.itemIndex,
      parentIndex: scope.parentIndex,
    );
  }

  List<Object?> _items(PaneRenderNode node, _PaneRenderStateScope scope) {
    final value = _property(node, kPaneRenderStateTargetItems, scope);
    if (value is Iterable && value is! String) {
      return value.toList(growable: false);
    }
    return const <Object?>[];
  }

  PaneActionBinding? _actionFor(PaneRenderNode node, String event) {
    for (final action in node.actionBindings) {
      if (action.event == event) {
        return action;
      }
    }
    return node.actionBindings.isEmpty ? null : node.actionBindings.first;
  }

  PaneActionBinding? _componentActionFor(
    PaneRenderNode node,
    String componentActionPortKey,
  ) {
    final normalizedPort = _trimmedOrNull(componentActionPortKey);
    if (normalizedPort == null) {
      return null;
    }
    for (final action in node.actionBindings) {
      if (_trimmedOrNull(action.componentActionPortKey) == normalizedPort) {
        return action;
      }
    }
    return null;
  }

  RenderComponentBuildData _componentBuildDataFor(
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    return RenderComponentBuildData(
      spec: widget.spec,
      node: node,
      paneContext: widget.paneContext,
      materializedState: widget.materializedState,
      inputsByPort: _componentInputsFor(node, scope),
      actionsByPort: _componentActionsFor(node),
      invokeActionPort: (componentActionPortKey) async {
        final action = _componentActionFor(node, componentActionPortKey);
        if (action == null) {
          throw StateError(
            'Render component `${node.componentRef ?? node.nodeKey}` has no '
            'action bound for port `$componentActionPortKey`.',
          );
        }
        await _invoke(action, scope);
      },
    );
  }

  Map<String, Object?> _componentInputsFor(
    PaneRenderNode node,
    _PaneRenderStateScope scope,
  ) {
    final inputs = <String, Object?>{};
    for (final binding in node.stateBindings) {
      final portKey = _trimmedOrNull(binding.componentInputPortKey);
      if (portKey == null) {
        continue;
      }
      final raw = _resolveBindingRaw(binding, scope);
      final value = paneRenderApplyStateTransform(binding, raw);
      inputs[portKey] = binding.targetProperty == kPaneRenderStateTargetMediaRef
          ? _mediaBindingValue(binding, scope, raw, value)
          : value;
    }
    return Map<String, Object?>.unmodifiable(inputs);
  }

  Map<String, PaneActionBinding> _componentActionsFor(PaneRenderNode node) {
    final actions = <String, PaneActionBinding>{};
    for (final action in node.actionBindings) {
      final portKey = _trimmedOrNull(action.componentActionPortKey);
      if (portKey == null) {
        continue;
      }
      actions.putIfAbsent(portKey, () => action);
    }
    return Map<String, PaneActionBinding>.unmodifiable(actions);
  }

  Future<void> _invoke(
    PaneActionBinding action,
    _PaneRenderStateScope scope,
  ) async {
    final invocationKey = _actionInvocationKey(action, scope);
    if (_pendingActionKeys.contains(invocationKey)) {
      return;
    }
    setState(() {
      _pendingActionKeys.add(invocationKey);
      _actionErrors.remove(invocationKey);
    });
    final invocation = PaneRenderActionInvocation(
      paneContext: widget.paneContext,
      actionBinding: action,
      payload: _payloadFor(action, scope),
    );
    try {
      final invoker = widget.onInvokeAction;
      if (invoker != null) {
        await invoker(invocation);
        return;
      }
      if (!mounted) {
        return;
      }
      final container = ProviderScope.containerOf(context, listen: false);
      final dispatcher = container.read(interfacePaneActionDispatcherProvider);
      await dispatcher.invokeRenderSpecAction(invocation);
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _actionErrors[invocationKey] = _actionErrorMessage(error);
      });
    } finally {
      if (mounted) {
        setState(() {
          _pendingActionKeys.remove(invocationKey);
        });
      }
    }
  }

  Map<String, dynamic> _payloadFor(
    PaneActionBinding action,
    _PaneRenderStateScope scope,
  ) {
    final payload = <String, dynamic>{};
    for (final binding in action.inputBindings) {
      final value = _payloadValueFor(binding, scope);
      if (value == null) {
        continue;
      }
      _setPayloadValue(payload, binding.payloadPath, value);
    }
    return payload;
  }

  Object? _payloadValueFor(
    PaneInputBinding binding,
    _PaneRenderStateScope scope,
  ) {
    final literal = binding.literalValue;
    if (literal != null) {
      return literal;
    }
    final sourceNodeKey = binding.sourceNodeKey;
    if (sourceNodeKey != null) {
      return _textInputs[sourceNodeKey]?.controller.text;
    }
    final sourceJsonPath = binding.sourceJsonPath;
    if (sourceJsonPath != null) {
      return paneRenderResolveStatePath(
        widget.materializedState,
        sourceJsonPath,
        item: scope.item,
        parentItem: scope.parentItem,
        itemIndex: scope.itemIndex,
        parentIndex: scope.parentIndex,
      );
    }
    return null;
  }

  String _actionInvocationKey(
    PaneActionBinding action,
    _PaneRenderStateScope scope,
  ) {
    if (scope.path.isEmpty) {
      return action.bindingKey;
    }
    return '${action.bindingKey}@${scope.path.join('.')}';
  }

  ButtonStyle? _buttonStyle(BuildContext context, PaneRenderNode node) {
    if (_styleToken(node, 'emphasis') != 'primary') {
      return null;
    }
    final theme = Theme.of(context);
    return ElevatedButton.styleFrom(
      elevation: 0,
      backgroundColor: theme.colorScheme.primaryContainer,
      foregroundColor: theme.colorScheme.onPrimaryContainer,
      disabledBackgroundColor: theme.colorScheme.surface.withAlpha(180),
      disabledForegroundColor: theme.colorScheme.onSurfaceVariant,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    );
  }

  String? _styleToken(PaneRenderNode node, String tokenKey) {
    for (final token in node.styleTokens) {
      if (token.tokenKey == tokenKey) {
        return token.tokenValue ?? token.tokenKey;
      }
    }
    return null;
  }
}

class _UnsupportedPaneRenderCapability {
  const _UnsupportedPaneRenderCapability({
    required this.kind,
    required this.key,
  });

  final String kind;
  final String key;

  String get label => '$kind:$key';
}

List<_UnsupportedPaneRenderCapability> _deduplicateCapabilities(
  Iterable<_UnsupportedPaneRenderCapability> capabilities,
) {
  final seen = <String>{};
  final result = <_UnsupportedPaneRenderCapability>[];
  for (final capability in capabilities) {
    final label = capability.label;
    if (seen.add(label)) {
      result.add(capability);
    }
  }
  return List<_UnsupportedPaneRenderCapability>.unmodifiable(result);
}

StorageMediaResolution? _mediaResolutionFromValue(Object? value) {
  if (value is StorageMediaResolution) {
    return value;
  }
  final json = _jsonObject(value);
  if (json == null || !json.containsKey('media_ref')) {
    return null;
  }
  try {
    return StorageMediaResolution.fromJson(json);
  } on Object {
    return null;
  }
}

StorageMediaRef? _mediaRefFromValue(Object? value) {
  if (value is StorageMediaRef) {
    return value;
  }
  final json = _jsonObject(value);
  if (json == null) {
    return null;
  }
  final nested = _jsonObject(json['media_ref'] ?? json['mediaRef']);
  if (nested != null) {
    try {
      return StorageMediaRef.fromJson(nested);
    } on Object {
      return null;
    }
  }
  try {
    return decodeInterfaceStorageMediaRef(json);
  } on Object {
    return null;
  }
}

String _mediaResolutionKey(
  PaneStateBinding binding,
  _PaneRenderStateScope scope,
  StorageMediaRef mediaRef,
) {
  return <String>[
    binding.bindingKey,
    scope.path.join('.'),
    mediaRef.objectId.uuid,
    mediaRef.variantKey ?? '',
    mediaRef.renditionKey ?? '',
    mediaRef.uri ?? '',
  ].join('|');
}

String? _renderableMediaSource(StorageMediaResolution? resolution) {
  if (resolution == null) {
    return null;
  }
  final httpUrl = _trimmedOrNull(resolution.httpUrl);
  if (httpUrl != null) {
    return httpUrl;
  }
  final uri = _trimmedOrNull(resolution.uri);
  if (uri == null) {
    return null;
  }
  final lower = uri.toLowerCase();
  if (lower.startsWith('http://') ||
      lower.startsWith('https://') ||
      lower.startsWith('data:image/')) {
    return uri;
  }
  return null;
}

Map<String, dynamic>? _jsonObject(Object? value) {
  if (value is Map<String, dynamic>) {
    return value;
  }
  if (value is Map) {
    final result = <String, dynamic>{};
    for (final entry in value.entries) {
      final key = entry.key;
      if (key is! String) {
        return null;
      }
      result[key] = entry.value;
    }
    return result;
  }
  return null;
}

double? _positiveDouble(String? value) {
  final parsed = double.tryParse(value ?? '');
  if (parsed == null || !parsed.isFinite || parsed <= 0) {
    return null;
  }
  return parsed;
}

String? _trimmedOrNull(String? value) {
  final text = value?.trim();
  if (text == null || text.isEmpty) {
    return null;
  }
  return text;
}

class _PaneRenderStateScope {
  const _PaneRenderStateScope({
    required this.materializedState,
    this.item,
    this.parentItem,
    this.itemIndex,
    this.parentIndex,
    this.path = const <int>[],
  });

  final InterfaceMaterializedPaneState? materializedState;
  final Object? item;
  final Object? parentItem;
  final int? itemIndex;
  final int? parentIndex;
  final List<int> path;

  _PaneRenderStateScope withItem(Object? nextItem, int nextIndex) {
    return _PaneRenderStateScope(
      materializedState: materializedState,
      parentItem: item,
      parentIndex: itemIndex,
      item: nextItem,
      itemIndex: nextIndex,
      path: List<int>.unmodifiable(<int>[...path, nextIndex]),
    );
  }
}

class _PaneRenderTextInputState {
  _PaneRenderTextInputState({
    required String canonicalValue,
    required VoidCallback onDraftChanged,
  })  : controller = TextEditingController(text: canonicalValue),
        _lastCanonicalValue = canonicalValue,
        _onDraftChanged = onDraftChanged {
    controller.addListener(_handleControllerChanged);
  }

  final TextEditingController controller;
  final VoidCallback _onDraftChanged;
  String _lastCanonicalValue;
  bool _hasLocalEdit = false;
  bool _applyingCanonicalValue = false;

  bool get hasLocalEdit => _hasLocalEdit;

  void syncFromCanonical(String nextValue) {
    if (controller.text == nextValue) {
      _lastCanonicalValue = nextValue;
      _hasLocalEdit = false;
      return;
    }
    if (_hasLocalEdit && nextValue == _lastCanonicalValue) {
      return;
    }
    _lastCanonicalValue = nextValue;
    _applyingCanonicalValue = true;
    controller.value = TextEditingValue(
      text: nextValue,
      selection: TextSelection.collapsed(offset: nextValue.length),
    );
    _applyingCanonicalValue = false;
    _hasLocalEdit = false;
  }

  void dispose() {
    controller
      ..removeListener(_handleControllerChanged)
      ..dispose();
  }

  void _handleControllerChanged() {
    if (_applyingCanonicalValue) {
      return;
    }
    final nextHasLocalEdit = controller.text != _lastCanonicalValue;
    if (_hasLocalEdit == nextHasLocalEdit) {
      return;
    }
    _hasLocalEdit = nextHasLocalEdit;
    _onDraftChanged();
  }
}

({Color background, Color foreground, Color outline}) _toneColors(
  ThemeData theme,
  String? tone,
) {
  final normalized = tone?.trim().toLowerCase();
  if (normalized == 'success') {
    final isDark = theme.brightness == Brightness.dark;
    return (
      background: isDark ? const Color(0xFF17361F) : const Color(0xFFE2F6E7),
      foreground: isDark ? const Color(0xFFA7E8B0) : const Color(0xFF17652A),
      outline: isDark ? const Color(0xFF27643A) : const Color(0xFF9CD7A7),
    );
  }
  if (normalized == 'danger' || normalized == 'error') {
    return (
      background: theme.colorScheme.errorContainer,
      foreground: theme.colorScheme.onErrorContainer,
      outline: theme.colorScheme.error.withAlpha(110),
    );
  }
  if (normalized == 'warning') {
    return (
      background: theme.colorScheme.tertiaryContainer,
      foreground: theme.colorScheme.onTertiaryContainer,
      outline: theme.colorScheme.tertiary.withAlpha(110),
    );
  }
  if (normalized == 'pending') {
    return (
      background: theme.colorScheme.primaryContainer,
      foreground: theme.colorScheme.onPrimaryContainer,
      outline: theme.colorScheme.primary.withAlpha(110),
    );
  }
  if (normalized == 'receipt') {
    return (
      background: theme.colorScheme.primaryContainer,
      foreground: theme.colorScheme.onPrimaryContainer,
      outline: theme.colorScheme.primary.withAlpha(110),
    );
  }
  if (normalized == 'neutral' || normalized == 'provenance') {
    return (
      background: theme.colorScheme.surfaceContainerHighest,
      foreground: theme.colorScheme.onSurfaceVariant,
      outline: theme.colorScheme.outlineVariant,
    );
  }
  return (
    background: theme.colorScheme.secondaryContainer,
    foreground: theme.colorScheme.onSecondaryContainer,
    outline: theme.colorScheme.outlineVariant,
  );
}

String _actionErrorMessage(Object error) {
  final text = error.toString().trim();
  if (text.isEmpty) {
    return 'Action failed';
  }
  return text;
}

void _setPayloadValue(Map<String, dynamic> payload, String path, Object value) {
  final segments = path
      .trim()
      .replaceFirst(RegExp(r'^\$\.'), '')
      .split('.')
      .where((segment) => segment.trim().isNotEmpty)
      .toList(growable: false);
  if (segments.isEmpty) {
    return;
  }
  var current = payload;
  for (final segment in segments.take(segments.length - 1)) {
    current = current.putIfAbsent(segment, () => <String, dynamic>{})
        as Map<String, dynamic>;
  }
  current[segments.last] = value;
}
