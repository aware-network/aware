import 'package:aware_shell/aware_shell.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid_value.dart';

void main() {
  PanePackageRegistry buildRegistry() {
    final registry = PanePackageRegistry();
    registry.registerPanePackage(
      panePackageId: UuidValue.fromString(
        '11111111-1111-1111-1111-111111111111',
      ),
      panePackageName: 'home-story-home-overview-pane',
      paneKind: 'home',
      factory: (context) => Text('mounted:${context.kind}:${context.paneId}'),
      capabilities: const runtime.PaneCapabilities(),
      displayInfo: const runtime.PaneDisplayInfo(
        paneKey: 'home',
        title: 'Home Overview',
        description: 'Home overview package',
      ),
    );
    return registry;
  }

  List<InterfaceShellSection> buildSections() {
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

  testWidgets('mounts registered pane packages into matching sections', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'configuration_map',
          sections: buildSections(),
          panePackageRegistry: buildRegistry(),
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'configuration_map',
              sectionKey: 'workspace',
              paneKind: 'home',
              panePackageId: UuidValue.fromString(
                '11111111-1111-1111-1111-111111111111',
              ),
              panePackageName: 'home-story-home-overview-pane',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              title: 'Home Overview',
              stateSourceKind: 'section_focus_scope_lane',
            ),
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'territory',
              sectionKey: 'workspace',
              paneKind: 'home',
              panePackageId: UuidValue.fromString(
                '11111111-1111-1111-1111-111111111111',
              ),
              panePackageName: 'home-story-home-overview-pane',
              paneConfigId: UuidValue.fromString(
                'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
              ),
              title: 'Ignored Other Layout Pane',
              stateSourceKind: 'section_focus_scope_lane',
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Workspace'), findsOneWidget);
    expect(
      find.text('mounted:home:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
      findsOneWidget,
    );
    expect(find.textContaining('Ignored Other Layout Pane'), findsNothing);
  });

  testWidgets('fills runtime sections to the available viewport height', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 900);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'configuration_map',
          sections: buildSections(),
          panePackageRegistry: buildRegistry(),
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'configuration_map',
              sectionKey: 'workspace',
              paneKind: 'home',
              panePackageId: UuidValue.fromString(
                '11111111-1111-1111-1111-111111111111',
              ),
              panePackageName: 'home-story-home-overview-pane',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              title: 'Home Overview',
              stateSourceKind: 'section_focus_scope_lane',
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    final workspaceHeight = tester
        .getSize(find.byKey(const Key('window-fullscreen-section-workspace')))
        .height;
    final workspaceTopLeft = tester.getTopLeft(
      find.byKey(const Key('window-fullscreen-section-workspace')),
    );
    final inspectorHeight = tester
        .getSize(find.byKey(const Key('window-fullscreen-section-inspector')))
        .height;

    expect(workspaceTopLeft.dx, closeTo(0, 1));
    expect(workspaceTopLeft.dy, closeTo(0, 1));
    expect(workspaceHeight, greaterThan(760));
    expect(inspectorHeight, greaterThan(760));
  });

  testWidgets(
    'shows placeholders for missing pane package identity and unregistered packages',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: InterfaceRuntimeShell(
            windowKey: 'main',
            layoutKey: 'configuration_map',
            sections: buildSections(),
            panePackageRegistry: buildRegistry(),
            resolvedPanes: <InterfaceResolvedPaneDescriptor>[
              InterfaceResolvedPaneDescriptor(
                windowKey: 'main',
                layoutKey: 'configuration_map',
                sectionKey: 'workspace',
                paneKind: 'door',
                title: 'Door Control',
                stateSourceKind: 'section_focus_scope_lane',
              ),
              InterfaceResolvedPaneDescriptor(
                windowKey: 'main',
                layoutKey: 'configuration_map',
                sectionKey: 'inspector',
                paneKind: 'tv',
                panePackageId: UuidValue.fromString(
                  '22222222-2222-2222-2222-222222222222',
                ),
                panePackageName: 'home-story-tv-status-pane',
                title: 'TV Status',
                stateSourceKind: 'section_focus_scope_lane',
              ),
            ],
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Workspace'), findsOneWidget);
      expect(find.text('Inspector'), findsOneWidget);
      expect(
        find.textContaining('Pane package identity is missing for `door`'),
        findsOneWidget,
      );
      expect(find.textContaining('home-story-tv-status-pane'), findsOneWidget);
    },
  );

  testWidgets('renders host pane contributions before package admission', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'bootstrap',
          layoutKey: 'bootstrap.panes',
          sections: const <InterfaceShellSection>[
            InterfaceShellSection(
              sectionKey: 'interface_admission',
              region: WindowFullscreenSectionRegion.stage,
              order: 0,
              title: 'Interface Admission',
            ),
          ],
          panePackageRegistry: PanePackageRegistry(),
          allowedActions: <InterfaceAllowedAction>[
            InterfaceAllowedAction(
              actionKey: 'interface_admission.create_interface',
              label: 'Create interface',
              enabled: false,
              reason: 'Interface Admission action execution is pending.',
            ),
          ],
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'bootstrap',
              layoutKey: 'bootstrap.panes',
              sectionKey: 'interface_admission',
              paneKind: 'interface_admission',
              title: 'Interface Admission',
              summary: 'Create, select, pair, or resume a canonical Interface.',
              narrativeKey: 'bootstrap.panes.interface_admission',
              stateSourceKind: 'host_pane_contribution',
              actionKeys: <String>['interface_admission.create_interface'],
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Interface Admission'), findsWidgets);
    expect(
      find.text('Create, select, pair, or resume a canonical Interface.'),
      findsOneWidget,
    );
    expect(
      find.widgetWithText(FilledButton, 'Create interface'),
      findsOneWidget,
    );
    expect(
      find.textContaining('Pane package identity is missing'),
      findsNothing,
    );
  });

  testWidgets('deduplicates shared disabled host action reasons', (
    tester,
  ) async {
    const sharedReason = 'Select and pairing require Interface transport.';
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'bootstrap',
          layoutKey: 'bootstrap.panes',
          sections: const <InterfaceShellSection>[
            InterfaceShellSection(
              sectionKey: 'interface_admission',
              region: WindowFullscreenSectionRegion.stage,
              order: 0,
              title: 'Interface Admission',
            ),
          ],
          panePackageRegistry: PanePackageRegistry(),
          allowedActions: <InterfaceAllowedAction>[
            InterfaceAllowedAction(
              actionKey: 'interface_admission.create_interface',
              label: 'Create interface',
              enabled: true,
              payloadSchemaHint: '{display_name?: string}',
            ),
            InterfaceAllowedAction(
              actionKey: 'interface_admission.select_interface',
              label: 'Select interface',
              enabled: false,
              reason: sharedReason,
            ),
            InterfaceAllowedAction(
              actionKey: 'interface_admission.request_pairing',
              label: 'Show pairing code',
              enabled: false,
              reason: sharedReason,
            ),
          ],
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'bootstrap',
              layoutKey: 'bootstrap.panes',
              sectionKey: 'interface_admission',
              paneKind: 'interface_admission',
              title: 'Interface Admission',
              summary: 'Create, select, pair, or resume a canonical Interface.',
              stateSourceKind: 'host_pane_contribution',
              actionKeys: <String>[
                'interface_admission.create_interface',
                'interface_admission.select_interface',
                'interface_admission.request_pairing',
              ],
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(
      find.widgetWithText(FilledButton, 'Create interface'),
      findsOneWidget,
    );
    expect(find.text(sharedReason), findsOneWidget);
    expect(find.text('{display_name?: string}'), findsNothing);
  });

  testWidgets('renders empty section copy when no panes are mounted', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'configuration_map',
          sections: buildSections(),
          panePackageRegistry: buildRegistry(),
          resolvedPanes: const <InterfaceResolvedPaneDescriptor>[],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Workspace'), findsOneWidget);
    expect(find.text('Inspector'), findsOneWidget);
    expect(
      find.text(
        'No mounted panes for section `workspace` in layout `configuration_map`.',
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        'No mounted panes for section `inspector` in layout `configuration_map`.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('passes lane identity and materialized host state to panes', (
    tester,
  ) async {
    final registry = PanePackageRegistry();
    registry.registerPanePackage(
      panePackageId: UuidValue.fromString(
        '11111111-1111-1111-1111-111111111111',
      ),
      panePackageName: 'identity-admission-pane',
      paneKind: 'identity_admission',
      factory: (context) {
        final state = context.parameters[kPaneParamMaterializedState]
            as InterfaceMaterializedPaneState?;
        return Text(
          [
            context.parameters[kPaneParamBranchId],
            context.parameters[kPaneParamStateProjectionHash],
            context.parameters[kPaneParamViewKey],
            context.parameters[kPaneParamViewRef],
            state?.status,
            state?.provenance['source_kind'],
          ].join('|'),
        );
      },
      capabilities: const runtime.PaneCapabilities(),
      displayInfo: const runtime.PaneDisplayInfo(
        paneKey: 'identity_admission',
        title: 'Identity Admission',
        description: 'Identity Admission',
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'coordination_center',
          sections: buildSections(),
          panePackageRegistry: registry,
          materializedPaneStates: <InterfaceMaterializedPaneState>[
            InterfaceMaterializedPaneState(
              paneStateKey:
                  'main:coordination_center:workspace:identity_admission:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:identity-hash',
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              branchId: UuidValue.fromString(
                'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
              ),
              projectionHash: 'identity-hash',
              status: 'materialized',
              state: const <String, dynamic>{},
              provenance: const <String, dynamic>{
                'source_kind': 'interface_host_fanout_materialization',
              },
            ),
          ],
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              panePackageId: UuidValue.fromString(
                '11111111-1111-1111-1111-111111111111',
              ),
              panePackageName: 'identity-admission-pane',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              branchId: UuidValue.fromString(
                'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
              ),
              projectionViewId: 'identity.profile.home',
              viewRef: 'aware_identity.profile.home.v1',
              projectionViewKey: 'profile.home.v1',
              stateSourceKind: 'section_focus_scope_lane',
              stateProjectionHash: 'identity-hash',
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(
      find.text(
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb|identity-hash|profile.home.v1|aware_identity.profile.home.v1|materialized|interface_host_fanout_materialization',
      ),
      findsOneWidget,
    );
  });

  testWidgets('renders declarative render specs before Dart pane packages', (
    tester,
  ) async {
    final spec = PaneRenderSpec(
      specId: 'identity-admission-render-spec-v0',
      name: 'identity_admission_default',
      specVersion: '0.1.0',
      paneKind: 'identity_admission',
      viewRef: 'aware_control_identity.identity.admission.v1',
      projectionViewKey: 'identity.admission.v1',
      rootNodeKey: 'root',
      nodes: const <PaneRenderNode>[
        PaneRenderNode(
          nodeKey: 'root',
          nodeKind: kPaneRenderNodeKindColumn,
          semanticRole: 'pane',
        ),
        PaneRenderNode(
          nodeKey: 'status',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindStatus,
          semanticRole: 'status',
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'status_text',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.status',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
      ],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'coordination_center',
          sections: buildSections(),
          panePackageRegistry: PanePackageRegistry(),
          renderSpecs: <PaneRenderSpec>[spec],
          materializedPaneStates: <InterfaceMaterializedPaneState>[
            InterfaceMaterializedPaneState(
              paneStateKey:
                  'main:coordination_center:workspace:identity_admission:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:identity-hash',
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              projectionHash: 'identity-hash',
              status: 'materialized',
              state: const <String, dynamic>{'status': 'ready'},
              provenance: const <String, dynamic>{},
            ),
          ],
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              viewRef: 'aware_control_identity.identity.admission.v1',
              projectionViewKey: 'identity.admission.v1',
              stateSourceKind: 'section_focus_scope_lane',
              stateProjectionHash: 'identity-hash',
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('ready'), findsOneWidget);
    expect(find.text('Workspace'), findsNothing);
    expect(
      find.textContaining('Pane package identity is missing'),
      findsNothing,
    );
  });

  testWidgets('reports shell and render-spec build tags through recorder', (
    tester,
  ) async {
    final builds = <String>[];
    final spec = PaneRenderSpec(
      specId: 'identity-admission-render-spec-v0',
      name: 'identity_admission_default',
      specVersion: '0.1.0',
      paneKind: 'identity_admission',
      viewRef: 'aware_control_identity.identity.admission.v1',
      projectionViewKey: 'identity.admission.v1',
      rootNodeKey: 'root',
      nodes: const <PaneRenderNode>[
        PaneRenderNode(
          nodeKey: 'root',
          nodeKind: kPaneRenderNodeKindColumn,
          semanticRole: 'pane',
        ),
        PaneRenderNode(
          nodeKey: 'status',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindStatus,
          semanticRole: 'status',
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'status_text',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.status',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
      ],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'coordination_center',
          sections: buildSections(),
          panePackageRegistry: PanePackageRegistry(),
          renderSpecs: <PaneRenderSpec>[spec],
          materializedPaneStates: <InterfaceMaterializedPaneState>[
            InterfaceMaterializedPaneState(
              paneStateKey:
                  'main:coordination_center:workspace:identity_admission:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:identity-hash',
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              projectionHash: 'identity-hash',
              status: 'materialized',
              state: const <String, dynamic>{'status': 'ready'},
              provenance: const <String, dynamic>{},
            ),
          ],
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              viewRef: 'aware_control_identity.identity.admission.v1',
              projectionViewKey: 'identity.admission.v1',
              stateSourceKind: 'section_focus_scope_lane',
              stateProjectionHash: 'identity-hash',
            ),
          ],
          onBuild: builds.add,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(builds, contains('InterfaceRuntimeShell'));
    expect(builds, contains('PaneRenderSpecWidget:identity_admission'));
  });

  testWidgets('keeps section title when multiple render specs mount together', (
    tester,
  ) async {
    final spec = PaneRenderSpec(
      specId: 'identity-admission-render-spec-v0',
      name: 'identity_admission_default',
      specVersion: '0.1.0',
      paneKind: 'identity_admission',
      viewRef: 'aware_control_identity.identity.admission.v1',
      projectionViewKey: 'identity.admission.v1',
      rootNodeKey: 'root',
      nodes: const <PaneRenderNode>[
        PaneRenderNode(
          nodeKey: 'root',
          nodeKind: kPaneRenderNodeKindColumn,
          semanticRole: 'pane',
        ),
        PaneRenderNode(
          nodeKey: 'status',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindStatus,
          semanticRole: 'status',
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'status_text',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.status',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
      ],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'coordination_center',
          sections: buildSections(),
          panePackageRegistry: PanePackageRegistry(),
          renderSpecs: <PaneRenderSpec>[spec],
          materializedPaneStates: <InterfaceMaterializedPaneState>[
            InterfaceMaterializedPaneState(
              paneStateKey:
                  'main:coordination_center:workspace:identity_admission:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:first-hash',
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              projectionHash: 'first-hash',
              status: 'materialized',
              state: const <String, dynamic>{'status': 'ready'},
              provenance: const <String, dynamic>{},
            ),
            InterfaceMaterializedPaneState(
              paneStateKey:
                  'main:coordination_center:workspace:identity_admission:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb:second-hash',
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
              ),
              projectionHash: 'second-hash',
              status: 'materialized',
              state: const <String, dynamic>{'status': 'pending'},
              provenance: const <String, dynamic>{},
            ),
          ],
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              viewRef: 'aware_control_identity.identity.admission.v1',
              projectionViewKey: 'identity.admission.v1',
              stateSourceKind: 'section_focus_scope_lane',
              stateProjectionHash: 'first-hash',
            ),
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
              ),
              viewRef: 'aware_control_identity.identity.admission.v1',
              projectionViewKey: 'identity.admission.v1',
              stateSourceKind: 'section_focus_scope_lane',
              stateProjectionHash: 'second-hash',
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Workspace'), findsOneWidget);
    expect(find.text('ready'), findsOneWidget);
    expect(find.text('pending'), findsOneWidget);
  });

  testWidgets(
    'matches materialized pane state when descriptor omits projection hash',
    (tester) async {
      final spec = PaneRenderSpec(
        specId: 'identity-admission-render-spec-v0',
        name: 'identity_admission_default',
        specVersion: '0.1.0',
        paneKind: 'identity_admission',
        viewRef: 'aware_control_identity.identity.admission.v1',
        projectionViewKey: 'identity.admission.v1',
        rootNodeKey: 'root',
        nodes: const <PaneRenderNode>[
          PaneRenderNode(
            nodeKey: 'root',
            nodeKind: kPaneRenderNodeKindColumn,
            semanticRole: 'pane',
          ),
          PaneRenderNode(
            nodeKey: 'status',
            parentNodeKey: 'root',
            nodeKind: kPaneRenderNodeKindStatus,
            semanticRole: 'status',
            stateBindings: <PaneStateBinding>[
              PaneStateBinding(
                bindingKey: 'status_text',
                targetProperty: kPaneRenderStateTargetText,
                jsonPath: r'$.status',
                transform: kPaneRenderStateTransformText,
              ),
            ],
          ),
        ],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: InterfaceRuntimeShell(
            windowKey: 'main',
            layoutKey: 'coordination_center',
            sections: buildSections(),
            panePackageRegistry: PanePackageRegistry(),
            renderSpecs: <PaneRenderSpec>[spec],
            materializedPaneStates: <InterfaceMaterializedPaneState>[
              InterfaceMaterializedPaneState(
                paneStateKey:
                    'main:coordination_center:workspace:identity_admission:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:identity-hash',
                windowKey: 'main',
                layoutKey: 'coordination_center',
                sectionKey: 'workspace',
                paneKind: 'identity_admission',
                paneConfigId: UuidValue.fromString(
                  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                ),
                projectionHash: 'identity-hash',
                status: 'materialized',
                state: const <String, dynamic>{'status': 'admitted'},
                provenance: const <String, dynamic>{},
              ),
            ],
            resolvedPanes: <InterfaceResolvedPaneDescriptor>[
              InterfaceResolvedPaneDescriptor(
                windowKey: 'main',
                layoutKey: 'coordination_center',
                sectionKey: 'workspace',
                paneKind: 'identity_admission',
                paneConfigId: UuidValue.fromString(
                  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                ),
                viewRef: 'aware_control_identity.identity.admission.v1',
                projectionViewKey: 'identity.admission.v1',
                stateSourceKind: 'section_focus_scope_lane',
              ),
            ],
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('admitted'), findsOneWidget);
    },
  );

  testWidgets('prefers dynamically overlaid render specs over static bundle', (
    tester,
  ) async {
    PaneRenderSpec specWithText(String text) {
      return PaneRenderSpec(
        specId: 'identity-admission-render-spec-v0',
        name: 'identity_admission_default',
        specVersion: '0.1.0',
        paneKind: 'identity_admission',
        viewRef: 'aware_control_identity.identity.admission.v1',
        projectionViewKey: 'identity.admission.v1',
        rootNodeKey: 'root',
        nodes: <PaneRenderNode>[
          PaneRenderNode(
            nodeKey: 'root',
            nodeKind: kPaneRenderNodeKindColumn,
            semanticRole: 'pane',
          ),
          PaneRenderNode(
            nodeKey: 'message',
            parentNodeKey: 'root',
            nodeKind: kPaneRenderNodeKindText,
            semanticRole: 'paragraph',
            text: text,
          ),
        ],
      );
    }

    final runtimePackage = InterfacePackageRuntime(
      interfacePackageId: 'aware-control-interface',
      interfacePackageName: 'aware-control-interface',
      panePackageRegistry: PanePackageRegistry(),
      renderSpecs: <PaneRenderSpec>[
        specWithText('static bundle render spec'),
      ],
    ).withRenderSpecOverlay(<PaneRenderSpec>[
      specWithText('committed OIG render spec'),
    ]);

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceRuntimeShell(
          windowKey: 'main',
          layoutKey: 'coordination_center',
          sections: buildSections(),
          panePackageRegistry: runtimePackage.panePackageRegistry,
          renderSpecs: runtimePackage.renderSpecs,
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneKind: 'identity_admission',
              paneConfigId: UuidValue.fromString(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
              ),
              viewRef: 'aware_control_identity.identity.admission.v1',
              projectionViewKey: 'identity.admission.v1',
              stateSourceKind: 'section_focus_scope_lane',
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('committed OIG render spec'), findsOneWidget);
    expect(find.text('static bundle render spec'), findsNothing);
  });
}
