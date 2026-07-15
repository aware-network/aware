library aware_interface_mount_status_pane;

import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter/material.dart';

const String _panePackageName = 'aware-interface-mount-status-pane';
const PaneKey _paneKind = 'interface_mount_status';

void registerPanePackage(PanePackageRegistry registry) {
  registry.registerPanePackage(
    panePackageId: stablePanePackageId(name: _panePackageName),
    panePackageName: _panePackageName,
    paneKind: _paneKind,
    capabilities: const runtime.PaneCapabilities(
      provides: {'interface.mount_status'},
      emits: {'interface.mount_status.event'},
      framePolicy: runtime.PaneFramePolicy.embedded,
    ),
    displayInfo: const runtime.PaneDisplayInfo(
      paneKey: _paneKind,
      title: 'Interface Mount Status',
      description:
          'Interface package mount status pane for the active host session.',
    ),
    factory: (paneContext) => _ControlPanePlaceholder(
      title: 'Interface Mount Status',
      subtitle: 'Mounted package state',
      detail: 'interface_mount_status:${paneContext.kind}',
    ),
  );
}

class _ControlPanePlaceholder extends StatelessWidget {
  const _ControlPanePlaceholder({
    required this.title,
    required this.subtitle,
    required this.detail,
  });

  final String title;
  final String subtitle;
  final String detail;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(title, style: theme.textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(subtitle, style: theme.textTheme.bodySmall),
          const SizedBox(height: 12),
          Text(detail, style: theme.textTheme.labelSmall),
        ],
      ),
    );
  }
}
