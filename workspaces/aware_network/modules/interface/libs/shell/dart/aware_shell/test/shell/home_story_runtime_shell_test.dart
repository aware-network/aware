import 'package:aware_shell/aware_shell.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

const String _windowKey = 'main';
const String _configurationMapLayoutKey = 'configuration_map';
const String _territoryLayoutKey = 'territory';

const String _homeOverviewPanePackageName = 'home-story-home-overview-pane';
const String _doorControlPanePackageName = 'home-story-door-control-pane';
const String _tvStatusPanePackageName = 'home-story-tv-status-pane';

const String _homeOverviewPaneName = 'home_overview';
const String _doorControlPaneName = 'door_control';
const String _tvStatusPaneName = 'tv_status';

final Uuid _uuid = Uuid();
final String _interfaceNamespace = _uuid.v5(
  Namespace.url.value,
  'aware://interface/v1',
);

UuidValue stablePaneConfigId({required String name}) {
  final nameNorm = name.toLowerCase().trim();
  return UuidValue.fromString(
    _uuid.v5(_interfaceNamespace, 'aware:pane_config:$nameNorm'),
  );
}

void main() {
  PanePackageRegistry buildHomeStoryPaneRegistry() {
    final registry = PanePackageRegistry();

    void register({
      required String panePackageName,
      required String paneKind,
      required String title,
    }) {
      registry.registerPanePackage(
        panePackageId: stablePanePackageId(name: panePackageName),
        panePackageName: panePackageName,
        paneKind: paneKind,
        capabilities: const runtime.PaneCapabilities(),
        displayInfo: runtime.PaneDisplayInfo(
          paneKey: paneKind,
          title: title,
          description: 'home_story proof package',
        ),
        factory: (context) => Text(
          'pkg:$panePackageName kind:${context.kind} '
          'section:${context.parameters['sectionKey']} pane:${context.paneId}',
        ),
      );
    }

    register(
      panePackageName: _homeOverviewPanePackageName,
      paneKind: 'home',
      title: 'Home Overview',
    );
    register(
      panePackageName: _doorControlPanePackageName,
      paneKind: 'door',
      title: 'Door Control',
    );
    register(
      panePackageName: _tvStatusPanePackageName,
      paneKind: 'tv',
      title: 'TV Status',
    );

    return registry;
  }

  List<InterfaceShellSection> buildConfigurationMapSections() {
    return const <InterfaceShellSection>[
      InterfaceShellSection(
        sectionKey: 'workspace',
        region: WindowFullscreenSectionRegion.stage,
        order: 0,
        title: 'Workspace',
      ),
      InterfaceShellSection(
        sectionKey: 'inspector',
        region: WindowFullscreenSectionRegion.trailing,
        order: 1,
        title: 'Inspector',
      ),
    ];
  }

  List<InterfaceShellSection> buildTerritorySections() {
    return const <InterfaceShellSection>[
      InterfaceShellSection(
        sectionKey: 'scene',
        region: WindowFullscreenSectionRegion.stage,
        order: 0,
        title: 'Scene',
      ),
      InterfaceShellSection(
        sectionKey: 'overlay_left',
        region: WindowFullscreenSectionRegion.leading,
        order: 1,
        title: 'Overlay Left',
      ),
      InterfaceShellSection(
        sectionKey: 'overlay_right',
        region: WindowFullscreenSectionRegion.trailing,
        order: 2,
        title: 'Overlay Right',
      ),
      InterfaceShellSection(
        sectionKey: 'inspector',
        region: WindowFullscreenSectionRegion.dock,
        order: 3,
        title: 'Inspector',
      ),
    ];
  }

  InterfaceResolvedPaneDescriptor buildResolvedPane({
    required String layoutKey,
    required String sectionKey,
    required String paneName,
    required String paneKind,
    required String panePackageName,
    required String title,
    required String viewRef,
    required String narrativeKey,
  }) {
    return InterfaceResolvedPaneDescriptor(
      windowKey: _windowKey,
      layoutKey: layoutKey,
      sectionKey: sectionKey,
      paneKind: paneKind,
      paneConfigId: stablePaneConfigId(name: paneName),
      panePackageId: stablePanePackageId(name: panePackageName),
      panePackageName: panePackageName,
      projectionViewId: viewRef,
      title: title,
      narrativeKey: narrativeKey,
      stateSourceKind: 'section_focus_scope_lane',
    );
  }

  testWidgets(
    'mounts the home_story configuration_map layout with home, door, and tv panes',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: InterfaceRuntimeShell(
            windowKey: _windowKey,
            layoutKey: _configurationMapLayoutKey,
            sections: buildConfigurationMapSections(),
            panePackageRegistry: buildHomeStoryPaneRegistry(),
            resolvedPanes: <InterfaceResolvedPaneDescriptor>[
              buildResolvedPane(
                layoutKey: _configurationMapLayoutKey,
                sectionKey: 'workspace',
                paneName: _homeOverviewPaneName,
                paneKind: 'home',
                panePackageName: _homeOverviewPanePackageName,
                title: 'Home Overview',
                viewRef: 'home_story.overview.home',
                narrativeKey: 'home.primary',
              ),
              buildResolvedPane(
                layoutKey: _configurationMapLayoutKey,
                sectionKey: 'inspector',
                paneName: _doorControlPaneName,
                paneKind: 'door',
                panePackageName: _doorControlPanePackageName,
                title: 'Door Control',
                viewRef: 'home_story.security.door',
                narrativeKey: 'security.control',
              ),
              buildResolvedPane(
                layoutKey: _configurationMapLayoutKey,
                sectionKey: 'inspector',
                paneName: _tvStatusPaneName,
                paneKind: 'tv',
                panePackageName: _tvStatusPanePackageName,
                title: 'TV Status',
                viewRef: 'home_story.entertainment.tv',
                narrativeKey: 'entertainment.control',
              ),
            ],
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Workspace'), findsOneWidget);
      expect(find.text('Inspector'), findsOneWidget);
      expect(
        find.text(
          'pkg:$_homeOverviewPanePackageName kind:home section:workspace '
          'pane:${stablePaneConfigId(name: _homeOverviewPaneName).uuid}',
        ),
        findsOneWidget,
      );
      expect(
        find.text(
          'pkg:$_doorControlPanePackageName kind:door section:inspector '
          'pane:${stablePaneConfigId(name: _doorControlPaneName).uuid}',
        ),
        findsOneWidget,
      );
      expect(
        find.text(
          'pkg:$_tvStatusPanePackageName kind:tv section:inspector '
          'pane:${stablePaneConfigId(name: _tvStatusPaneName).uuid}',
        ),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    'mounts the home_story territory layout while preserving the empty scene substrate',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: InterfaceRuntimeShell(
            windowKey: _windowKey,
            layoutKey: _territoryLayoutKey,
            sections: buildTerritorySections(),
            panePackageRegistry: buildHomeStoryPaneRegistry(),
            resolvedPanes: <InterfaceResolvedPaneDescriptor>[
              buildResolvedPane(
                layoutKey: _territoryLayoutKey,
                sectionKey: 'overlay_left',
                paneName: _doorControlPaneName,
                paneKind: 'door',
                panePackageName: _doorControlPanePackageName,
                title: 'Door Control',
                viewRef: 'home_story.security.door',
                narrativeKey: 'security.control',
              ),
              buildResolvedPane(
                layoutKey: _territoryLayoutKey,
                sectionKey: 'overlay_right',
                paneName: _tvStatusPaneName,
                paneKind: 'tv',
                panePackageName: _tvStatusPanePackageName,
                title: 'TV Status',
                viewRef: 'home_story.entertainment.tv',
                narrativeKey: 'entertainment.control',
              ),
              buildResolvedPane(
                layoutKey: _territoryLayoutKey,
                sectionKey: 'inspector',
                paneName: _homeOverviewPaneName,
                paneKind: 'home',
                panePackageName: _homeOverviewPanePackageName,
                title: 'Home Overview',
                viewRef: 'home_story.overview.home',
                narrativeKey: 'home.primary',
              ),
            ],
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Scene'), findsOneWidget);
      expect(
        find.text(
          'No mounted panes for section `scene` in layout `territory`.',
        ),
        findsOneWidget,
      );
      expect(
        find.text(
          'pkg:$_doorControlPanePackageName kind:door section:overlay_left '
          'pane:${stablePaneConfigId(name: _doorControlPaneName).uuid}',
        ),
        findsOneWidget,
      );
      expect(
        find.text(
          'pkg:$_tvStatusPanePackageName kind:tv section:overlay_right '
          'pane:${stablePaneConfigId(name: _tvStatusPaneName).uuid}',
        ),
        findsOneWidget,
      );
      expect(
        find.text(
          'pkg:$_homeOverviewPanePackageName kind:home section:inspector '
          'pane:${stablePaneConfigId(name: _homeOverviewPaneName).uuid}',
        ),
        findsOneWidget,
      );
    },
  );
}
