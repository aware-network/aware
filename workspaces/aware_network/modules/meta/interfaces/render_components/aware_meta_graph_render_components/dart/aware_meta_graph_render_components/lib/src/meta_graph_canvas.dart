import 'dart:async';
import 'dart:math' as math;

import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/material.dart';

const awareMetaGraphCanvasComponentRef = 'aware.meta.graph.canvas';

const awareMetaGraphInputGraphSnapshot = 'graph_snapshot';
const awareMetaGraphInputObjectConfigGraphRef = 'object_config_graph_ref';
const awareMetaGraphInputObjectProjectionGraphRef =
    'object_projection_graph_ref';
const awareMetaGraphInputObjectInstanceGraphRef = 'object_instance_graph_ref';
const awareMetaGraphInputObjectInstanceGraphBranchRef =
    'object_instance_graph_branch_ref';
const awareMetaGraphInputObjectInstanceGraphCommitRef =
    'object_instance_graph_commit_ref';
const awareMetaGraphInputSelectedIdentity = 'selected_identity';
const awareMetaGraphInputViewportState = 'viewport_state';

const awareMetaGraphActionSelectIdentity = 'select_identity';
const awareMetaGraphActionActivateIdentity = 'activate_identity';
const awareMetaGraphActionRequestFocusTransition = 'request_focus_transition';
const awareMetaGraphActionSetViewport = 'set_viewport';
const awareMetaGraphActionOpenBranch = 'open_branch';
const awareMetaGraphActionCompareCommit = 'compare_commit';

void registerRenderComponents(RenderComponentRegistryBuilder registry) {
  registry.register(
    RenderComponentRegistration(
      componentRef: awareMetaGraphCanvasComponentRef,
      displayName: 'Meta graph canvas',
      builder: _buildMetaGraphCanvas,
    ),
  );
}

Widget _buildMetaGraphCanvas(
  BuildContext context,
  RenderComponentBuildData component,
) {
  final snapshot = AwareMetaGraphSnapshot.fromInput(
    component.input(awareMetaGraphInputGraphSnapshot),
  );
  return AwareMetaGraphCanvas(
    snapshot: snapshot,
    selectedIdentity: _stringInput(
      component.input(awareMetaGraphInputSelectedIdentity),
    ),
    onSelectIdentity: component.hasAction(awareMetaGraphActionSelectIdentity)
        ? (_) => component.invokeActionPort(awareMetaGraphActionSelectIdentity)
        : null,
  );
}

class AwareMetaGraphCanvas extends StatelessWidget {
  const AwareMetaGraphCanvas({
    required this.snapshot,
    super.key,
    this.selectedIdentity,
    this.onSelectIdentity,
  });

  final AwareMetaGraphSnapshot snapshot;
  final String? selectedIdentity;
  final Future<void> Function(AwareMetaGraphNode node)? onSelectIdentity;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (snapshot.nodes.isEmpty) {
      return Text(
        'No graph snapshot',
        style: theme.textTheme.bodyMedium?.copyWith(
          color: theme.colorScheme.onSurfaceVariant,
          fontStyle: FontStyle.italic,
        ),
      );
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final size = Size(
          constraints.maxWidth.isFinite ? constraints.maxWidth : 560,
          constraints.maxHeight.isFinite && constraints.maxHeight > 0
              ? constraints.maxHeight
              : 320,
        );
        final layout = _layoutNodes(snapshot.nodes, size);
        return SizedBox(
          width: double.infinity,
          height: size.height,
          child: Stack(
            children: <Widget>[
              Positioned.fill(
                child: CustomPaint(
                  painter: _MetaGraphCanvasPainter(
                    snapshot: snapshot,
                    layout: layout,
                    selectedIdentity: selectedIdentity,
                    colorScheme: theme.colorScheme,
                  ),
                ),
              ),
              for (final node in snapshot.nodes)
                _MetaGraphNodeLabel(
                  node: node,
                  offset: layout[node.id] ?? Offset.zero,
                  selected: _identityMatches(node, selectedIdentity),
                  onTap: onSelectIdentity == null
                      ? null
                      : () => unawaited(onSelectIdentity!(node)),
                ),
            ],
          ),
        );
      },
    );
  }
}

class AwareMetaGraphSnapshot {
  const AwareMetaGraphSnapshot({required this.nodes, required this.edges});

  factory AwareMetaGraphSnapshot.fromInput(Object? input) {
    final payload = _mapInput(input);
    if (payload == null) {
      return const AwareMetaGraphSnapshot(nodes: [], edges: []);
    }
    final nodes = _listInput(payload['nodes'])
        .map(_mapInput)
        .whereType<Map<String, Object?>>()
        .map(AwareMetaGraphNode.fromMap)
        .where((node) => node.id.isNotEmpty)
        .toList(growable: false);
    final edges = _listInput(payload['edges'])
        .map(_mapInput)
        .whereType<Map<String, Object?>>()
        .map(AwareMetaGraphEdge.fromMap)
        .where((edge) => edge.id.isNotEmpty)
        .toList(growable: false);
    return AwareMetaGraphSnapshot(nodes: nodes, edges: edges);
  }

  final List<AwareMetaGraphNode> nodes;
  final List<AwareMetaGraphEdge> edges;
}

class AwareMetaGraphNode {
  const AwareMetaGraphNode({
    required this.id,
    required this.label,
    this.fqn,
    this.namespace,
    this.symbol,
    this.objectKind,
    this.stableIdentity,
    this.positionHint,
  });

  factory AwareMetaGraphNode.fromMap(Map<String, Object?> payload) {
    final id = _stringInput(payload['id']) ?? '';
    return AwareMetaGraphNode(
      id: id,
      label: _stringInput(payload['label']) ?? id,
      fqn: _stringInput(payload['fqn']),
      namespace: _stringInput(payload['namespace']),
      symbol: _stringInput(payload['symbol']),
      objectKind: _stringInput(payload['object_kind']),
      stableIdentity: _stringInput(payload['stable_identity']),
      positionHint: _offsetHint(payload['position_hint']),
    );
  }

  final String id;
  final String label;
  final String? fqn;
  final String? namespace;
  final String? symbol;
  final String? objectKind;
  final String? stableIdentity;
  final Offset? positionHint;
}

class AwareMetaGraphEdge {
  const AwareMetaGraphEdge({
    required this.id,
    required this.sourceNodeId,
    required this.targetNodeId,
    this.relationshipKind,
    this.label,
  });

  factory AwareMetaGraphEdge.fromMap(Map<String, Object?> payload) {
    final sourceNodeId =
        _stringInput(payload['source_node_id']) ??
        _stringInput(payload['source']) ??
        '';
    final targetNodeId =
        _stringInput(payload['target_node_id']) ??
        _stringInput(payload['target']) ??
        '';
    return AwareMetaGraphEdge(
      id: _stringInput(payload['id']) ?? '$sourceNodeId->$targetNodeId',
      sourceNodeId: sourceNodeId,
      targetNodeId: targetNodeId,
      relationshipKind: _stringInput(payload['relationship_kind']),
      label: _stringInput(payload['label']),
    );
  }

  final String id;
  final String sourceNodeId;
  final String targetNodeId;
  final String? relationshipKind;
  final String? label;
}

class _MetaGraphNodeLabel extends StatelessWidget {
  const _MetaGraphNodeLabel({
    required this.node,
    required this.offset,
    required this.selected,
    this.onTap,
  });

  final AwareMetaGraphNode node;
  final Offset offset;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    return Positioned(
      left: math.max(8, offset.dx - 58),
      top: math.max(8, offset.dy - 18),
      width: 116,
      child: Semantics(
        button: onTap != null,
        label: node.label,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(8),
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: selected
                  ? colorScheme.primaryContainer
                  : colorScheme.surfaceContainerHighest,
              border: Border.all(
                color: selected ? colorScheme.primary : colorScheme.outline,
              ),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
              child: Text(
                node.label,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
                style: theme.textTheme.labelMedium?.copyWith(
                  color: selected
                      ? colorScheme.onPrimaryContainer
                      : colorScheme.onSurface,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _MetaGraphCanvasPainter extends CustomPainter {
  const _MetaGraphCanvasPainter({
    required this.snapshot,
    required this.layout,
    required this.colorScheme,
    this.selectedIdentity,
  });

  final AwareMetaGraphSnapshot snapshot;
  final Map<String, Offset> layout;
  final String? selectedIdentity;
  final ColorScheme colorScheme;

  @override
  void paint(Canvas canvas, Size size) {
    final edgePaint = Paint()
      ..color = colorScheme.outlineVariant
      ..strokeWidth = 1.4
      ..style = PaintingStyle.stroke;
    final selectedEdgePaint = Paint()
      ..color = colorScheme.primary
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    final selectedNodeIds = snapshot.nodes
        .where((node) => _identityMatches(node, selectedIdentity))
        .map((node) => node.id)
        .toSet();

    for (final edge in snapshot.edges) {
      final source = layout[edge.sourceNodeId];
      final target = layout[edge.targetNodeId];
      if (source == null || target == null) {
        continue;
      }
      final selected =
          selectedNodeIds.contains(edge.sourceNodeId) ||
          selectedNodeIds.contains(edge.targetNodeId);
      canvas.drawLine(source, target, selected ? selectedEdgePaint : edgePaint);
    }

    for (final node in snapshot.nodes) {
      final center = layout[node.id];
      if (center == null) {
        continue;
      }
      final selected = _identityMatches(node, selectedIdentity);
      final fill = Paint()
        ..color = selected
            ? colorScheme.primary
            : colorScheme.secondaryContainer
        ..style = PaintingStyle.fill;
      final stroke = Paint()
        ..color = selected ? colorScheme.primary : colorScheme.outline
        ..strokeWidth = selected ? 2.6 : 1.4
        ..style = PaintingStyle.stroke;
      canvas
        ..drawCircle(center, selected ? 12 : 9, fill)
        ..drawCircle(center, selected ? 12 : 9, stroke);
    }
  }

  @override
  bool shouldRepaint(covariant _MetaGraphCanvasPainter oldDelegate) {
    return oldDelegate.snapshot != snapshot ||
        oldDelegate.layout != layout ||
        oldDelegate.selectedIdentity != selectedIdentity ||
        oldDelegate.colorScheme != colorScheme;
  }
}

Map<String, Offset> _layoutNodes(List<AwareMetaGraphNode> nodes, Size size) {
  final result = <String, Offset>{};
  final center = Offset(size.width / 2, size.height / 2);
  final radius = math.max(72.0, math.min(size.width, size.height) * 0.34);
  for (var index = 0; index < nodes.length; index += 1) {
    final node = nodes[index];
    final hinted = node.positionHint;
    if (hinted != null) {
      result[node.id] = _scaleHint(hinted, size);
      continue;
    }
    final angle = nodes.length == 1
        ? -math.pi / 2
        : (-math.pi / 2) + (index * 2 * math.pi / nodes.length);
    result[node.id] = Offset(
      center.dx + math.cos(angle) * radius,
      center.dy + math.sin(angle) * radius,
    );
  }
  return Map<String, Offset>.unmodifiable(result);
}

Offset _scaleHint(Offset hint, Size size) {
  final x = hint.dx.abs() <= 1 ? hint.dx * size.width : hint.dx;
  final y = hint.dy.abs() <= 1 ? hint.dy * size.height : hint.dy;
  return Offset(
    x.clamp(16.0, math.max(16.0, size.width - 16)),
    y.clamp(16.0, math.max(16.0, size.height - 16)),
  );
}

bool _identityMatches(AwareMetaGraphNode node, String? identity) {
  final selected = identity?.trim();
  if (selected == null || selected.isEmpty) {
    return false;
  }
  return node.id == selected ||
      node.stableIdentity == selected ||
      node.fqn == selected ||
      node.symbol == selected;
}

Map<String, Object?>? _mapInput(Object? input) {
  if (input is Map<String, Object?>) {
    return input;
  }
  if (input is Map) {
    return input.map((key, value) => MapEntry('$key', value));
  }
  return null;
}

List<Object?> _listInput(Object? input) {
  if (input is List<Object?>) {
    return input;
  }
  if (input is List) {
    return List<Object?>.from(input);
  }
  return const <Object?>[];
}

String? _stringInput(Object? input) {
  final text = input?.toString().trim();
  if (text == null || text.isEmpty) {
    return null;
  }
  return text;
}

Offset? _offsetHint(Object? input) {
  final payload = _mapInput(input);
  if (payload == null) {
    return null;
  }
  final x = _doubleInput(payload['x']);
  final y = _doubleInput(payload['y']);
  if (x == null || y == null) {
    return null;
  }
  return Offset(x, y);
}

double? _doubleInput(Object? input) {
  if (input is num) {
    return input.toDouble();
  }
  if (input is String) {
    return double.tryParse(input.trim());
  }
  return null;
}
