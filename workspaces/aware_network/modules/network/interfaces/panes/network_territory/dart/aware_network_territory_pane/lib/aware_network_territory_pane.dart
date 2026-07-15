library aware_network_territory_pane;

import 'package:aware_network_service_api/aware_network_service_api.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:aware_widgets/aware_widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

const String _panePackageName = 'aware-network-territory-pane';
const PaneKey _paneKind = 'network_territory';

void registerPanePackage(PanePackageRegistry registry) {
  registry.registerPanePackage(
    panePackageId: stablePanePackageId(name: _panePackageName),
    panePackageName: _panePackageName,
    paneKind: _paneKind,
    capabilities: const runtime.PaneCapabilities(
      provides: {'network.territory'},
      emits: {'network.environment_attention'},
      framePolicy: runtime.PaneFramePolicy.embedded,
    ),
    displayInfo: const runtime.PaneDisplayInfo(
      paneKey: _paneKind,
      title: 'Network Territory',
      description:
          'Live Network nodes, environments, hosted services, and peers.',
    ),
    factory: (paneContext) => NetworkTerritoryPane(paneContext: paneContext),
  );
}

class NetworkTerritoryPane extends ConsumerWidget {
  const NetworkTerritoryPane({super.key, required this.paneContext});

  final PaneContext paneContext;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final materialized =
        interfacePaneMaterializedStateForContext(ref, paneContext);
    final snapshot =
        _NetworkTerritorySnapshot.fromMaterializedState(materialized);

    return Material(
      color: Colors.transparent,
      child: Padding(
        padding: const EdgeInsets.all(4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            const _RoleBadge(
              index: '03',
              label: 'NETWORK TERRITORY',
              color: AwareColors.connectionRole,
            ),
            const SizedBox(height: 10),
            _Header(snapshot: snapshot),
            const SizedBox(height: 14),
            if (snapshot.error != null)
              _PanePanel(
                child: Text(
                  snapshot.error!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: Colors.white.withValues(alpha: 0.84),
                  ),
                ),
              )
            else if (snapshot.nodes.isEmpty)
              _PanePanel(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  child: Text(
                    snapshot.emptyMessage,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: Colors.white.withValues(alpha: 0.62),
                      height: 1.4,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              )
            else
              for (final node in snapshot.nodes) ...[
                _NodeTerritoryCard(node: node),
                const SizedBox(height: 8),
              ],
            if (snapshot.authoritySourceUrl != null) ...[
              const SizedBox(height: 8),
              Text(
                'Source: ${snapshot.authoritySourceUrl}',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: Colors.white.withValues(alpha: 0.42),
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.snapshot});

  final _NetworkTerritorySnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Live nodes and environments.',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: Colors.white.withValues(alpha: 0.94),
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                snapshot.summary ?? 'Territory published by Network Service.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: Colors.white.withValues(alpha: 0.66),
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 12),
        _StatusChip(snapshot: snapshot),
      ],
    );
  }
}

class _NodeTerritoryCard extends StatelessWidget {
  const _NodeTerritoryCard({required this.node});

  final NetworkTerritoryNodeViewStateV1 node;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final route = node.node;
    final title = route?.hostname ?? route?.baseUrl ?? 'unknown node';
    final subtitle = route?.baseUrl ?? _nodeIdShort(route?.nodeId);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AwareColors.connectionRole.withValues(alpha: 0.18),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: theme.textTheme.titleSmall?.copyWith(
                        color: Colors.white.withValues(alpha: 0.92),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 3),
                      Text(
                        subtitle,
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: Colors.white.withValues(alpha: 0.48),
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 10),
              _StatusPill(label: route?.status ?? 'active'),
            ],
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _CountChip(
                icon: Icons.public_outlined,
                label: '${node.environments.length} envs',
              ),
              _CountChip(
                icon: Icons.account_tree_outlined,
                label: '${node.hostedServices.length} services',
              ),
              _CountChip(
                icon: Icons.hub_outlined,
                label: '${node.peers.length} peers',
              ),
            ],
          ),
          if (node.environments.isNotEmpty) ...[
            const SizedBox(height: 12),
            for (final environment in node.environments.take(3)) ...[
              _EnvironmentRow(environment: environment),
              const SizedBox(height: 6),
            ],
          ],
          if (node.hostedServices.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final service in node.hostedServices.take(4))
                  _ServiceChip(service: service),
              ],
            ),
          ],
        ],
      ),
    );
  }

  String? _nodeIdShort(String? nodeId) {
    if (nodeId == null || nodeId.isEmpty) {
      return null;
    }
    return nodeId.length <= 8 ? nodeId : nodeId.substring(0, 8);
  }
}

class _EnvironmentRow extends StatelessWidget {
  const _EnvironmentRow({required this.environment});

  final NetworkTerritoryEnvironmentViewStateV1 environment;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final title = environment.environmentTitle ??
        environment.environmentKey ??
        environment.environmentId ??
        'environment';
    final experiences = environment.experienceNames.take(2).join(', ');
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.025),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Row(
        children: [
          Icon(
            Icons.public_outlined,
            size: 15,
            color: AwareColors.connectionRole.withValues(alpha: 0.9),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: Colors.white.withValues(alpha: 0.86),
                    fontWeight: FontWeight.w600,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                if (experiences.isNotEmpty)
                  Text(
                    experiences,
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: Colors.white.withValues(alpha: 0.5),
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          _StatusPill(label: environment.status),
        ],
      ),
    );
  }
}

class _ServiceChip extends StatelessWidget {
  const _ServiceChip({required this.service});

  final NetworkTerritoryHostedServiceViewStateV1 service;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final label = service.serviceName ?? 'service';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: AwareColors.hubRole.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AwareColors.hubRole.withValues(alpha: 0.22)),
      ),
      child: Text(
        label,
        style: theme.textTheme.labelSmall?.copyWith(
          color: Colors.white.withValues(alpha: 0.78),
        ),
      ),
    );
  }
}

class _CountChip extends StatelessWidget {
  const _CountChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.white.withValues(alpha: 0.11)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 13,
            color: Colors.white.withValues(alpha: 0.55),
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: Colors.white.withValues(alpha: 0.72),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.snapshot});

  final _NetworkTerritorySnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (label, color) = _resolve();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.55)),
      ),
      child: Text(
        label,
        style: theme.textTheme.labelSmall?.copyWith(
          color: Colors.white.withValues(alpha: 0.94),
        ),
      ),
    );
  }

  (String, Color) _resolve() {
    if (snapshot.error != null) {
      return ('UNAVAILABLE', AwareColors.warning);
    }
    if (snapshot.status == 'waiting' || snapshot.nodes.isEmpty) {
      return ('WAITING', Colors.white.withValues(alpha: 0.5));
    }
    return (
      'LIVE · ${snapshot.nodes.length} nodes',
      AwareColors.connectionRole
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isActive = label.toLowerCase() == 'active';
    final color = isActive ? AwareColors.success : AwareColors.warning;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.45)),
      ),
      child: Text(
        label.toUpperCase(),
        style: theme.textTheme.labelSmall?.copyWith(
          color: Colors.white.withValues(alpha: 0.86),
        ),
      ),
    );
  }
}

class _RoleBadge extends StatelessWidget {
  const _RoleBadge({
    required this.index,
    required this.label,
    required this.color,
  });

  final String index;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 6,
          height: 6,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: color.withValues(alpha: 0.6),
                blurRadius: 6,
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '$index · $label',
          style: theme.textTheme.labelSmall?.copyWith(
            color: Colors.white.withValues(alpha: 0.7),
          ),
        ),
      ],
    );
  }
}

class _PanePanel extends StatelessWidget {
  const _PanePanel({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AwareColors.connectionRole.withValues(alpha: 0.22),
        ),
      ),
      child: child,
    );
  }
}

class _NetworkTerritorySnapshot {
  const _NetworkTerritorySnapshot({
    required this.status,
    required this.nodes,
    required this.emptyMessage,
    this.summary,
    this.authoritySourceUrl,
    this.error,
  });

  factory _NetworkTerritorySnapshot.fromMaterializedState(
    InterfaceMaterializedPaneState? state,
  ) {
    if (state == null) {
      return const _NetworkTerritorySnapshot(
        status: 'waiting',
        nodes: <NetworkTerritoryNodeViewStateV1>[],
        emptyMessage: 'Connecting to Network Service…',
      );
    }
    final encoded = state.state;
    if (encoded.isEmpty) {
      return const _NetworkTerritorySnapshot(
        status: 'waiting',
        nodes: <NetworkTerritoryNodeViewStateV1>[],
        emptyMessage: 'No Network territory has been published yet',
      );
    }
    try {
      final viewState = NetworkTerritoryDiscoveryViewStateV1.fromJson(
        encoded.cast<String, dynamic>(),
      );
      return _NetworkTerritorySnapshot(
        status: viewState.status,
        nodes: viewState.nodes,
        emptyMessage: viewState.emptyMessage,
        summary: viewState.summary,
        authoritySourceUrl: viewState.authoritySourceUrl,
        error: viewState.error,
      );
    } catch (error) {
      return _NetworkTerritorySnapshot(
        status: 'error',
        nodes: const <NetworkTerritoryNodeViewStateV1>[],
        emptyMessage: 'No Network territory has been published yet',
        error: error.toString(),
      );
    }
  }

  final String status;
  final List<NetworkTerritoryNodeViewStateV1> nodes;
  final String emptyMessage;
  final String? summary;
  final String? authoritySourceUrl;
  final String? error;
}
