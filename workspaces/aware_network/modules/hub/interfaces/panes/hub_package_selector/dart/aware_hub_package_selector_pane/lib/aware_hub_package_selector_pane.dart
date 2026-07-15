library aware_hub_package_selector_pane;

import 'package:aware_hub_service_api/aware_hub_service_api.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:aware_widgets/aware_widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

const String _panePackageName = 'aware-hub-package-selector-pane';
const PaneKey _paneKind = 'hub_package_selector';

void registerPanePackage(PanePackageRegistry registry) {
  registry.registerPanePackage(
    panePackageId: stablePanePackageId(name: _panePackageName),
    panePackageName: _panePackageName,
    paneKind: _paneKind,
    capabilities: const runtime.PaneCapabilities(
      provides: {'hub.public_discovery'},
      emits: {'hub.package_attention'},
      framePolicy: runtime.PaneFramePolicy.embedded,
    ),
    displayInfo: const runtime.PaneDisplayInfo(
      paneKey: _paneKind,
      title: 'Hub Discovery',
      description:
          'Public Hub channel-head map of available CodePackages on the Aware Network.',
    ),
    factory: (paneContext) => HubPackageSelectorPane(paneContext: paneContext),
  );
}

/// Hub public discovery pane — the Map of public channel heads on the network.
///
/// v0 renders [HubPublicDiscoveryViewStateV1] entries as a card list. The
/// long-term endgame is for this surface to evolve into the canonical
/// `OCGGraphViewer`-driven map (Hub → WorkspaceRevision → OCGPackage → OCG)
/// once OCG Projection coverage is in place.
class HubPackageSelectorPane extends ConsumerWidget {
  const HubPackageSelectorPane({super.key, required this.paneContext});

  final PaneContext paneContext;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final materialized =
        interfacePaneMaterializedStateForContext(ref, paneContext);
    final snapshot = _HubDiscoverySnapshot.fromMaterializedState(materialized);

    return Material(
      color: Colors.transparent,
      child: Padding(
        padding: const EdgeInsets.all(4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            const _RoleBadge(
              index: '02',
              label: 'THE AWARE NETWORK',
              color: AwareColors.hubRole,
            ),
            const SizedBox(height: 10),
            _buildHeader(theme, snapshot),
            const SizedBox(height: 14),
            _buildBody(theme, snapshot),
            const SizedBox(height: 12),
            _buildAuthorityFooter(theme, snapshot),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme, _HubDiscoverySnapshot snapshot) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Public packages on the network.',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: Colors.white.withValues(alpha: 0.94),
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                snapshot.summary ??
                    'Channel heads published by the Hub authority.',
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

  Widget _buildBody(ThemeData theme, _HubDiscoverySnapshot snapshot) {
    if (snapshot.error != null) {
      return _PanePanel(
        roleColor: AwareColors.hubRole,
        child: Text(
          snapshot.error!,
          style: theme.textTheme.bodySmall?.copyWith(
            color: Colors.white.withValues(alpha: 0.84),
          ),
        ),
      );
    }
    if (snapshot.entries.isEmpty) {
      return _PanePanel(
        roleColor: AwareColors.hubRole,
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
      );
    }
    return Column(
      children: [
        for (final entry in snapshot.entries) ...[
          _ChannelHeadCard(entry: entry),
          const SizedBox(height: 8),
        ],
      ],
    );
  }

  Widget _buildAuthorityFooter(
      ThemeData theme, _HubDiscoverySnapshot snapshot) {
    final authority = snapshot.authoritySourceUrl;
    if (authority == null || authority.isEmpty) {
      return const SizedBox.shrink();
    }
    return Text(
      'Source: $authority',
      style: theme.textTheme.labelSmall?.copyWith(
        color: Colors.white.withValues(alpha: 0.42),
        letterSpacing: 0.6,
      ),
      textAlign: TextAlign.center,
    );
  }
}

class _ChannelHeadCard extends StatelessWidget {
  const _ChannelHeadCard({required this.entry});

  final HubPublicDiscoveryEntryV1 entry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final languageColor = _languageColor(entry.language);
    final descriptor = entry.descriptor;
    final version = descriptor?.version;
    final surface = entry.surface ?? descriptor?.surface;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: AwareColors.hubRole.withValues(alpha: 0.18),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  entry.packageName ?? 'unknown package',
                  style: theme.textTheme.titleSmall?.copyWith(
                    color: languageColor,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.2,
                  ),
                ),
                const SizedBox(height: 4),
                Wrap(
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 8,
                  runSpacing: 4,
                  children: [
                    if (entry.language != null)
                      _MetaChip(
                        icon: Icons.code_outlined,
                        label: entry.language!,
                        color: languageColor,
                      ),
                    if (surface != null)
                      _MetaChip(
                        icon: Icons.layers_outlined,
                        label: surface,
                      ),
                    if (version != null)
                      _MetaChip(
                        icon: Icons.tag_outlined,
                        label: 'v$version',
                      ),
                    _RevisionDot(revisionId: entry.revisionId),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          _ChannelPill(channel: entry.channel),
        ],
      ),
    );
  }

  Color _languageColor(String? language) {
    switch (language?.toLowerCase()) {
      case 'python':
        return AwareColors.cyan;
      case 'dart':
        return AwareColors.violet;
      case 'sql':
        return AwareColors.pink;
      default:
        return Colors.white.withValues(alpha: 0.86);
    }
  }
}

class _ChannelPill extends StatelessWidget {
  const _ChannelPill({required this.channel});

  final String channel;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final lower = channel.toLowerCase();
    final color = lower == 'stable'
        ? AwareColors.hubRole
        : lower == 'next'
            ? AwareColors.pink
            : Colors.white.withValues(alpha: 0.5);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.62)),
      ),
      child: Text(
        channel.toUpperCase(),
        style: theme.textTheme.labelSmall?.copyWith(
          color: Colors.white.withValues(alpha: 0.94),
          letterSpacing: 0.8,
        ),
      ),
    );
  }
}

class _RevisionDot extends StatelessWidget {
  const _RevisionDot({required this.revisionId});

  final String? revisionId;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final value = revisionId;
    if (value == null || value.isEmpty) {
      return const SizedBox.shrink();
    }
    final shortId = value.length <= 8 ? value : value.substring(0, 8);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          Icons.commit_outlined,
          size: 13,
          color: Colors.white.withValues(alpha: 0.45),
        ),
        const SizedBox(width: 3),
        Text(
          shortId,
          style: theme.textTheme.labelSmall?.copyWith(
            color: Colors.white.withValues(alpha: 0.55),
            fontFeatures: const [FontFeature.tabularFigures()],
          ),
        ),
      ],
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({
    required this.icon,
    required this.label,
    this.color,
  });

  final IconData icon;
  final String label;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tint = color ?? Colors.white.withValues(alpha: 0.62);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: tint),
          const SizedBox(width: 4),
          Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: Colors.white.withValues(alpha: 0.8),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.snapshot});

  final _HubDiscoverySnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (label, color) = _resolve(snapshot);
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
          letterSpacing: 0.8,
        ),
      ),
    );
  }

  (String, Color) _resolve(_HubDiscoverySnapshot s) {
    if (s.error != null) {
      return ('UNAVAILABLE', AwareColors.warning);
    }
    if (s.status == 'waiting' || s.entries.isEmpty) {
      return ('WAITING', Colors.white.withValues(alpha: 0.5));
    }
    return ('LIVE · ${s.entries.length} packages', AwareColors.hubRole);
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
            letterSpacing: 1.4,
          ),
        ),
      ],
    );
  }
}

class _PanePanel extends StatelessWidget {
  const _PanePanel({required this.child, required this.roleColor});

  final Widget child;
  final Color roleColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: roleColor.withValues(alpha: 0.22)),
      ),
      child: child,
    );
  }
}

class _HubDiscoverySnapshot {
  const _HubDiscoverySnapshot({
    required this.status,
    required this.entries,
    required this.emptyMessage,
    this.summary,
    this.authoritySourceUrl,
    this.error,
  });

  factory _HubDiscoverySnapshot.fromMaterializedState(
    InterfaceMaterializedPaneState? state,
  ) {
    if (state == null) {
      return const _HubDiscoverySnapshot(
        status: 'waiting',
        entries: <HubPublicDiscoveryEntryV1>[],
        emptyMessage: 'Connecting to the Hub authority…',
      );
    }
    final encoded = state.state;
    if (encoded.isEmpty) {
      return const _HubDiscoverySnapshot(
        status: 'waiting',
        entries: <HubPublicDiscoveryEntryV1>[],
        emptyMessage: 'No public Hub packages published yet',
      );
    }
    try {
      final viewState = HubPublicDiscoveryViewStateV1.fromJson(
        encoded.cast<String, dynamic>(),
      );
      return _HubDiscoverySnapshot(
        status: viewState.status,
        entries: viewState.entries,
        emptyMessage: viewState.emptyMessage,
        summary: viewState.summary,
        authoritySourceUrl: viewState.authoritySourceUrl,
        error: viewState.error,
      );
    } catch (error) {
      return _HubDiscoverySnapshot(
        status: 'error',
        entries: const <HubPublicDiscoveryEntryV1>[],
        emptyMessage: 'No public Hub packages published yet',
        error: error.toString(),
      );
    }
  }

  final String status;
  final List<HubPublicDiscoveryEntryV1> entries;
  final String emptyMessage;
  final String? summary;
  final String? authoritySourceUrl;
  final String? error;
}
