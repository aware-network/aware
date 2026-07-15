import 'package:aware_shell/aware_shell.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid_value.dart';

void main() {
  PanePackageRegistry buildRegistry() {
    final registry = PanePackageRegistry();
    registry.registerPanePackage(
      panePackageId: UuidValue.fromString(
        'd919c1a0-46f1-5d0c-894e-555ea7d1dd41',
      ),
      panePackageName: 'aware-workspace-representation-selector-pane',
      paneKind: 'workspace_representation_selector',
      factory: (context) =>
          Text('mounted:${context.kind}:${context.paneId}:selector'),
      capabilities: const runtime.PaneCapabilities(),
      displayInfo: const runtime.PaneDisplayInfo(
        paneKey: 'workspace_representation_selector',
        title: 'Representation Selector',
        description: 'Workspace representation selector package',
      ),
    );
    registry.registerPanePackage(
      panePackageId: UuidValue.fromString(
        'fdff6abd-599b-5069-a6fb-66bbb6654e6d',
      ),
      panePackageName: 'aware-workspace-control-pane',
      paneKind: 'workspace',
      factory: (paneContext) => Consumer(
        builder: (buildContext, ref, _) {
          final namespace = ref.watch(interfacePaneApiNamespaceProvider);
          final transport = ref.watch(interfacePaneApiTransportProvider);
          final client = ref.watch(interfacePaneApiClientProvider);
          return Text(
            'mounted:${paneContext.kind}:${paneContext.paneId}:$namespace:${transport.runtimeType}:${client.runtimeType}',
          );
        },
      ),
      capabilities: const runtime.PaneCapabilities(),
      displayInfo: const runtime.PaneDisplayInfo(
        paneKey: 'workspace',
        title: 'Workspace Control',
        description: 'Workspace control package',
      ),
    );
    return registry;
  }

  InterfaceWindowLayoutState buildWindowLayoutState() {
    return InterfaceWindowLayoutState(
      sourceKind: 'committed_oig',
      windowKey: 'main',
      layoutKey: 'workspace_control',
      frameMode: 'grid',
      stale: false,
      sections: <InterfaceWindowLayoutSectionState>[
        InterfaceWindowLayoutSectionState(
          sectionKey: 'orchestration',
          order: 0,
          flex: 0.8,
          isVisible: true,
        ),
        InterfaceWindowLayoutSectionState(
          sectionKey: 'center',
          order: 1,
          flex: 2.4,
          isVisible: true,
        ),
        InterfaceWindowLayoutSectionState(
          sectionKey: 'inspector',
          order: 2,
          flex: 1.2,
          isVisible: true,
        ),
        InterfaceWindowLayoutSectionState(
          sectionKey: 'console',
          order: 3,
          flex: 0.5,
          isVisible: true,
        ),
      ],
    );
  }

  InterfaceTransportState buildTransportState() {
    return InterfaceTransportState(
      available: true,
      registered: true,
      authenticated: true,
    );
  }

  InterfaceBackendState buildBackendState() {
    return InterfaceBackendState(
      available: true,
      databaseExists: false,
      opgCount: 0,
      projectionBundleAvailable: true,
      projectionPlanCount: 0,
      tableCount: 0,
      reason: 'test',
    );
  }

  InterfaceMaterializedPaneState buildEnvironmentNavigatorState() {
    return InterfaceMaterializedPaneState(
      paneStateKey: 'shell:environment_navigation:environment_navigator',
      windowKey: 'shell',
      layoutKey: 'environment_navigation',
      sectionKey: 'environment_navigator',
      paneKind: 'environment_navigator',
      projectionViewId: 'environment.navigator.v1',
      status: 'ready',
      state: const <String, dynamic>{
        'environment_id': '11111111-1111-4111-8111-111111111111',
        'title': 'Dogfood Environment',
        'status': 'ready',
        'ready': true,
        'selected_process_id': '22222222-2222-4222-8222-222222222222',
        'selected_thread_id': '33333333-3333-4333-8333-333333333333',
        'processes': <Map<String, dynamic>>[
          <String, dynamic>{
            'process_id': '22222222-2222-4222-8222-222222222222',
            'process_key': 'coordination',
            'title': 'Coordination',
            'thread_count': 1,
            'is_selected': true,
            'threads': <Map<String, dynamic>>[
              <String, dynamic>{
                'thread_id': '33333333-3333-4333-8333-333333333333',
                'thread_key': 'conversation',
                'title': 'Conversation',
                'attachment_count': 0,
                'active_attachment_count': 0,
                'is_selected': true,
              },
            ],
          },
        ],
        'status_blocks': <Map<String, dynamic>>[],
        'empty_message': 'No environment threads available.',
        'provenance': <String, dynamic>{'source': 'test'},
      },
      provenance: const <String, dynamic>{
        'view_ref': 'aware_environments.environment.navigator.v1',
        'projection_view_key': 'environment.navigator.v1',
      },
    );
  }

  InterfaceMaterializedPaneState buildThreadLayoutState({
    String threadKey = 'conversation',
    String activeLayoutKey = 'coordination_conversation',
    List<Map<String, dynamic>> sections = const <Map<String, dynamic>>[
      <String, dynamic>{
        'section_key': 'conversation',
        'title': 'Conversation',
        'description': 'Shared coordination conversation.',
        'order': 0,
        'flex': 1.0,
        'is_visible': true,
        'pane_key': 'conversation',
        'view_ref': 'aware_coordination.conversation.v1',
        'view_key': 'conversation.v1',
      },
    ],
  }) {
    return InterfaceMaterializedPaneState(
      paneStateKey: 'shell:environment_navigation:thread_layout',
      windowKey: 'main',
      layoutKey: activeLayoutKey,
      sectionKey: 'thread_layout',
      paneKind: 'thread_layout',
      projectionViewId: 'thread.layout.v1',
      status: 'ready',
      state: <String, dynamic>{
        'environment_id': '11111111-1111-4111-8111-111111111111',
        'process_id': '22222222-2222-4222-8222-222222222222',
        'process_key': 'coordination',
        'thread_id': '33333333-3333-4333-8333-333333333333',
        'thread_key': threadKey,
        'title': 'Conversation',
        'status': 'ready',
        'active_layout_id': '44444444-4444-4444-8444-444444444444',
        'active_layout_key': activeLayoutKey,
        'layouts': <Map<String, dynamic>>[
          <String, dynamic>{
            'layout_id': '44444444-4444-4444-8444-444444444444',
            'layout_key': activeLayoutKey,
            'title': 'Conversation',
            'is_active': true,
            'sections': sections,
          },
        ],
        'sections': sections,
        'attachments': <Map<String, dynamic>>[],
        'empty_message': '',
        'provenance': <String, dynamic>{'source': 'test'},
      },
      provenance: const <String, dynamic>{
        'view_ref': 'aware_environments.thread.layout.v1',
        'projection_view_key': 'thread.layout.v1',
      },
    );
  }

  InterfaceHostState buildHostState({
    bool typedWindowLayout = false,
    bool includeEnvironmentNavigator = false,
    bool includeThreadLayout = false,
    bool attentionLayout = false,
  }) {
    final materializedPaneStates = <InterfaceMaterializedPaneState>[
      if (includeEnvironmentNavigator) buildEnvironmentNavigatorState(),
      if (includeThreadLayout) buildThreadLayoutState(),
    ];
    return InterfaceHostState(
      hostLabel: 'interface-flutter',
      namespace: 'flutter-test',
      started: true,
      transport: buildTransportState(),
      runtime: InterfaceRuntimeState(
        backend: buildBackendState(),
        windowLayout: typedWindowLayout ? buildWindowLayoutState() : null,
        layoutStates: <InterfaceRuntimeLayoutState>[
          InterfaceRuntimeLayoutState(
            layoutKey: 'workspace_control',
            label: 'Workspace',
            isDefault: true,
            isActive: true,
          ),
          InterfaceRuntimeLayoutState(
            layoutKey: 'graph_view',
            label: 'Graph',
            isDefault: false,
            isActive: false,
          ),
          InterfaceRuntimeLayoutState(
            layoutKey: 'code_view',
            label: 'Code',
            isDefault: false,
            isActive: false,
          ),
        ],
        resolvedView: InterfaceResolvedView(
          experienceKey: 'aware_workspace',
          projectionViewId: 'aware_workspace.control.main',
          hostPayload: typedWindowLayout
              ? const <String, dynamic>{}
              : <String, dynamic>{
                  'window_layout': <String, dynamic>{
                    'window_key': 'main',
                    'layout_key': 'workspace_control',
                    'frame_mode': 'grid',
                    if (attentionLayout)
                      'active_layout_transition_id':
                          'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
                    if (attentionLayout)
                      'active_topology_transition_id':
                          'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
                    'sections': <Map<String, dynamic>>[
                      <String, dynamic>{
                        'section_key': 'orchestration',
                        'order': 0,
                        'flex': 0.8,
                        if (attentionLayout) ...<String, dynamic>{
                          'layout_config_section_config_id':
                              '11111111-1111-4111-8111-111111111111',
                          'weight_micros': 100000,
                        },
                      },
                      <String, dynamic>{
                        'section_key': 'center',
                        'order': 1,
                        'flex': 2.4,
                        if (attentionLayout) ...<String, dynamic>{
                          'layout_config_section_config_id':
                              '22222222-2222-4222-8222-222222222222',
                          'weight_micros': 500000,
                        },
                      },
                      <String, dynamic>{
                        'section_key': 'inspector',
                        'order': 2,
                        'flex': 1.2,
                        if (attentionLayout) ...<String, dynamic>{
                          'layout_config_section_config_id':
                              '33333333-3333-4333-8333-333333333333',
                          'weight_micros': 200000,
                        },
                      },
                      <String, dynamic>{
                        'section_key': 'console',
                        'order': 3,
                        'flex': 0.5,
                        if (attentionLayout) ...<String, dynamic>{
                          'layout_config_section_config_id':
                              '44444444-4444-4444-8444-444444444444',
                          'weight_micros': 200000,
                        },
                      },
                    ],
                  },
                },
        ),
        resolvedPanes: <InterfaceResolvedPaneDescriptor>[
          InterfaceResolvedPaneDescriptor(
            windowKey: 'main',
            layoutKey: 'workspace_control',
            sectionKey: 'orchestration',
            paneKind: 'workspace_representation_selector',
            panePackageId: UuidValue.fromString(
              'd919c1a0-46f1-5d0c-894e-555ea7d1dd41',
            ),
            panePackageName: 'aware-workspace-representation-selector-pane',
            paneConfigId: UuidValue.fromString(
              '7fbba548-0930-4c59-9ef5-0437ac4bbc9e',
            ),
            title: 'Representation Selector',
            stateSourceKind: 'section_focus_scope_lane',
          ),
          InterfaceResolvedPaneDescriptor(
            windowKey: 'main',
            layoutKey: 'workspace_control',
            sectionKey: 'center',
            paneKind: 'workspace',
            panePackageId: UuidValue.fromString(
              'fdff6abd-599b-5069-a6fb-66bbb6654e6d',
            ),
            panePackageName: 'aware-workspace-control-pane',
            paneConfigId: UuidValue.fromString(
              '17cde6d7-0d52-54d7-b86d-a3812368dff4',
            ),
            title: 'Workspace Control',
            stateSourceKind: 'section_focus_scope_lane',
          ),
        ],
        materializedPaneStates: materializedPaneStates,
      ),
    );
  }

  const authoritySectionA = '6a29b4a8-122b-5f4d-8463-18a5a460c2e5';
  const authoritySectionB = 'a43471db-a82f-516f-916b-42abd81158aa';
  const authoritySectionC = '7773eccc-9159-5c5c-b7dd-0e8c3a788d91';
  const authorityTopologyT0 = 'a45b3f02-20af-5f52-8906-b87d95d0728f';
  const authorityTopologyT1 = '58554ebc-96db-5d59-9545-2e9f64ace18b';
  const authorityTopologyT2 = '5d72496a-b8b5-5c81-8b3a-3d96bb4f03d4';
  const authorityTopologyRemote = 'ffffffff-ffff-4fff-8fff-ffffffffffff';
  const authorityGeometryG0 = '185b2dcb-fd67-53af-a2d6-a659861393d9';
  const authorityPanePackageId = '99999999-9999-4999-8999-999999999991';

  InterfaceHostState buildAuthorityHostState({
    required String topologyTransitionId,
    required List<String> activeSectionIds,
    String? layoutTransitionId,
  }) {
    const sectionKeys = <String, String>{
      authoritySectionA: 'navigation',
      authoritySectionB: 'stage',
      authoritySectionC: 'inspector',
    };
    const weights = <String, int>{
      authoritySectionA: 300000,
      authoritySectionB: 400000,
      authoritySectionC: 300000,
    };
    InterfaceWindowLayoutSectionState section(
      String sectionId,
      int order,
    ) {
      return InterfaceWindowLayoutSectionState(
        sectionKey: sectionKeys[sectionId]!,
        layoutConfigSectionConfigId: UuidValue.fromString(sectionId),
        order: order,
        flex: weights[sectionId]! / windowLayoutWeightMicrosTotal,
        weightMicros: weights[sectionId],
        isVisible: true,
        isCollapsed: false,
      );
    }

    final base = buildHostState(typedWindowLayout: true);
    final runtime = base.runtime!;
    return base.copyWith(
      runtime: runtime.copyWith(
        windowLayout: InterfaceWindowLayoutState(
          sourceKind: 'attention_runtime_mount',
          windowKey: 'main',
          layoutKey: 'shared',
          activeLayoutTransitionId: layoutTransitionId == null
              ? null
              : UuidValue.fromString(layoutTransitionId),
          activeTopologyTransitionId:
              UuidValue.fromString(topologyTransitionId),
          frameMode: 'grid',
          admittedSections: <InterfaceWindowLayoutSectionState>[
            section(authoritySectionA, 0),
            section(authoritySectionB, 1),
            section(authoritySectionC, 2),
          ],
          sections: <InterfaceWindowLayoutSectionState>[
            for (final (order, sectionId) in activeSectionIds.indexed)
              section(sectionId, order),
          ],
        ),
        resolvedPanes: <InterfaceResolvedPaneDescriptor>[
          for (final sectionId in <String>[
            authoritySectionA,
            authoritySectionB,
            authoritySectionC,
          ])
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'shared',
              sectionKey: sectionKeys[sectionId]!,
              paneKind: 'authority_section',
              panePackageId: UuidValue.fromString(authorityPanePackageId),
              panePackageName: 'attention-authority-section-pane',
              paneConfigId: UuidValue.fromString(sectionId),
              title: 'Authority ${sectionKeys[sectionId]}',
              stateSourceKind: 'attention_runtime_mount',
            ),
        ],
      ),
    );
  }

  PanePackageRegistry buildAuthorityRegistry() {
    final registry = PanePackageRegistry();
    registry.registerPanePackage(
      panePackageId: UuidValue.fromString(authorityPanePackageId),
      panePackageName: 'attention-authority-section-pane',
      paneKind: 'authority_section',
      factory: (paneContext) {
        final sectionId = paneContext.paneId.toString();
        final label = switch (sectionId) {
          authoritySectionA => 'A',
          authoritySectionB => 'B',
          authoritySectionC => 'C',
          _ => '?',
        };
        return Builder(
          builder: (context) {
            final topology = WindowLayoutTopologyScope.of(context);
            return Column(
              children: <Widget>[
                Text('Authority Section $label'),
                if (sectionId == authoritySectionA) ...<Widget>[
                  TextButton(
                    key: const Key('preview-authority-t1'),
                    onPressed: () {
                      topology.beginPreview();
                      topology.previewMove(authoritySectionC, 0);
                      topology.previewRemove(authoritySectionB);
                    },
                    child: const Text('Preview T1'),
                  ),
                  TextButton(
                    key: const Key('preview-authority-t2'),
                    onPressed: () {
                      topology.beginPreview();
                      topology.previewReadd(authoritySectionB, atIndex: 1);
                    },
                    child: const Text('Preview T2'),
                  ),
                  TextButton(
                    key: const Key('commit-authority-topology'),
                    onPressed: topology.commitPreview,
                    child: const Text('Commit topology'),
                  ),
                ],
              ],
            );
          },
        );
      },
      capabilities: const runtime.PaneCapabilities(),
      displayInfo: const runtime.PaneDisplayInfo(
        paneKey: 'authority_section',
        title: 'Attention Authority Section',
        description: 'Row 101 Attention authority fixture section',
      ),
    );
    return registry;
  }

  InterfaceMaterializedPaneState buildCachedState({
    String paneStateKey =
        'main:coordination_center:workspace:identity_admission:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa:identity-hash',
    String label = 'Cached',
  }) {
    return InterfaceMaterializedPaneState(
      paneStateKey: paneStateKey,
      windowKey: 'main',
      layoutKey: 'coordination_center',
      sectionKey: 'workspace',
      paneKind: 'identity_admission',
      paneConfigId: UuidValue.fromString(
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      ),
      focusScopeId: UuidValue.fromString(
        'cccccccc-cccc-cccc-cccc-cccccccccccc',
      ),
      branchId: UuidValue.fromString('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'),
      projectionViewId: 'identity.profile.home',
      projectionHash: 'identity-hash',
      status: 'materialized',
      state: <String, dynamic>{'label': label},
      provenance: const <String, dynamic>{
        'view_ref': 'aware_identity.profile.home.v1',
        'projection_view_key': 'profile.home.v1',
      },
    );
  }

  InterfaceHostState buildCacheHostState({
    List<InterfaceMaterializedPaneState> materializedPaneStates =
        const <InterfaceMaterializedPaneState>[],
  }) {
    return InterfaceHostState(
      hostLabel: 'interface-flutter',
      namespace: 'flutter-test',
      environmentId: UuidValue.fromString(
        '11111111-1111-4111-8111-111111111111',
      ),
      environmentConfigId: UuidValue.fromString(
        '22222222-2222-4222-8222-222222222222',
      ),
      started: true,
      transport: buildTransportState(),
      runtime: InterfaceRuntimeState(
        backend: buildBackendState(),
        resolvedView: InterfaceResolvedView(
          experienceKey: 'aware_control_identity',
          interfacePackageId: UuidValue.fromString(
            '33333333-3333-4333-8333-333333333333',
          ),
          interfacePackageName: 'aware-control-interface',
          projectionViewId: 'aware_control_identity.main',
          hostPayload: <String, dynamic>{
            'window_layout': <String, dynamic>{
              'window_key': 'main',
              'layout_key': 'coordination_center',
              'frame_mode': 'grid',
              'sections': <Map<String, dynamic>>[
                <String, dynamic>{'section_key': 'workspace', 'order': 0},
              ],
            },
          },
        ),
        resolvedPanes: <InterfaceResolvedPaneDescriptor>[
          InterfaceResolvedPaneDescriptor(
            windowKey: 'main',
            layoutKey: 'coordination_center',
            sectionKey: 'workspace',
            paneKind: 'identity_admission',
            panePackageId: UuidValue.fromString(
              '99999999-9999-4999-8999-999999999999',
            ),
            panePackageName: 'identity-admission-pane',
            paneConfigId: UuidValue.fromString(
              'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            ),
            focusScopeId: UuidValue.fromString(
              'cccccccc-cccc-cccc-cccc-cccccccccccc',
            ),
            branchId: UuidValue.fromString(
              'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
            ),
            projectionViewId: 'identity.profile.home',
            viewRef: 'aware_identity.profile.home.v1',
            projectionViewKey: 'profile.home.v1',
            title: 'Identity Admission',
            stateSourceKind: 'section_focus_scope_lane',
            stateProjectionHash: 'identity-hash',
          ),
        ],
        materializedPaneStates: materializedPaneStates,
      ),
    );
  }

  testWidgets('mounts host runtime shell panes from host window layout payload',
      (
    tester,
  ) async {
    final registry = buildRegistry();
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceHostRuntimeShell(
          hostState: buildHostState(),
          panePackageRegistry: registry,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.byType(ChoiceChip), findsNothing);
    expect(find.text('Orchestration'), findsOneWidget);
    expect(find.text('Center'), findsOneWidget);
    expect(find.text('Inspector'), findsOneWidget);
    expect(find.text('Console'), findsOneWidget);
    expect(
      find.text(
        'mounted:workspace_representation_selector:7fbba548-0930-4c59-9ef5-0437ac4bbc9e:selector',
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        'mounted:workspace:17cde6d7-0d52-54d7-b86d-a3812368dff4:flutter-test:InterfaceSdkAwareApiTransport:AwareApiClient',
      ),
      findsOneWidget,
    );
    final frame = tester.widget<WindowFullscreenSectionFrame>(
      find.byType(WindowFullscreenSectionFrame),
    );
    expect(
      frame.sections.firstWhere((section) => section.id == 'center').flex,
      2.4,
    );
  });

  testWidgets('reports host and runtime shell build tags through recorder', (
    tester,
  ) async {
    final builds = <String>[];
    final registry = buildRegistry();

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceHostRuntimeShell(
          hostState: buildHostState(),
          panePackageRegistry: registry,
          onBuild: builds.add,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(builds, contains('InterfaceHostRuntimeShell'));
    expect(builds, contains('InterfaceRuntimeShell'));
  });

  testWidgets('production Host shell commits one full stable-id vector', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 900);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final commits = <WindowLayoutTransitionCommitIntent>[];

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceHostRuntimeShell(
          hostState: buildHostState(attentionLayout: true),
          panePackageRegistry: buildRegistry(),
          clientIntentIdFactory: () => 'host-drag-1',
          onLayoutTransitionCommit: (intent) async => commits.add(intent),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final handle = find.byKey(const Key('window-layout-resize-leading-stage'));
    final gesture = await tester.startGesture(tester.getCenter(handle));
    await gesture.moveBy(const Offset(80, 0));
    await tester.pump();
    expect(commits, isEmpty);

    await gesture.up();
    await tester.pumpAndSettle();

    expect(commits, hasLength(1));
    expect(commits.single.clientIntentId, 'host-drag-1');
    expect(
      commits.single.expectedPreviousTransitionId,
      'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    );
    expect(
      commits.single.topologyTransitionId,
      'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    );
    expect(
      commits.single.sectionStates.map((section) => section.sectionId),
      <String>[
        '11111111-1111-4111-8111-111111111111',
        '22222222-2222-4222-8222-222222222222',
        '33333333-3333-4333-8333-333333333333',
        '44444444-4444-4444-8444-444444444444',
      ],
    );
    expect(
      commits.single.sectionStates.fold<int>(
        0,
        (sum, section) => sum + section.weightMicros,
      ),
      windowLayoutWeightMicrosTotal,
    );
  });

  testWidgets('production Host shell calls provider once at drag end', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 900);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final hostState = buildHostState(attentionLayout: true);
    final notifier = _RecordingLayoutTransitionHostStateNotifier(hostState);

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          interfaceHostStateProvider.overrideWith(() => notifier),
        ],
        child: MaterialApp(
          home: InterfaceHostRuntimeShell(
            hostState: hostState,
            panePackageRegistry: buildRegistry(),
            clientIntentIdFactory: () => 'host-provider-drag-1',
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final handle = find.byKey(const Key('window-layout-resize-leading-stage'));
    final gesture = await tester.startGesture(tester.getCenter(handle));
    await gesture.moveBy(const Offset(80, 0));
    await tester.pump();
    expect(notifier.commits, isEmpty);

    await gesture.up();
    await tester.pumpAndSettle();

    expect(notifier.commits, hasLength(1));
    expect(notifier.commits.single.clientIntentId, 'host-provider-drag-1');
    expect(
      notifier.commits.single.topologyTransitionId?.uuid,
      'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    );
    expect(notifier.commits.single.sectionStates, hasLength(4));
    expect(
      notifier.commits.single.sectionStates.fold<int>(
        0,
        (sum, section) => sum + section.weightMicros,
      ),
      windowLayoutWeightMicrosTotal,
    );
  });

  testWidgets(
    'production Host shell previews row-101 topology locally and reconciles watched authority',
    (tester) async {
      tester.view.devicePixelRatio = 1.0;
      tester.view.physicalSize = const Size(1440, 900);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final notifier = _AuthorityHostStateNotifier(
        buildAuthorityHostState(
          topologyTransitionId: authorityTopologyT0,
          layoutTransitionId: authorityGeometryG0,
          activeSectionIds: const <String>[
            authoritySectionA,
            authoritySectionB,
            authoritySectionC,
          ],
        ),
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: <Override>[
            interfaceHostStateProvider.overrideWith(() => notifier),
          ],
          child: MaterialApp(
            home: Consumer(
              builder: (context, ref, _) {
                final hostState = ref.watch(interfaceHostStateProvider);
                return hostState.when(
                  data: (value) => InterfaceHostRuntimeShell(
                    hostState: value,
                    panePackageRegistry: buildAuthorityRegistry(),
                    clientIntentIdFactory: () =>
                        'flutter-authority-${notifier.intentSequence++}',
                  ),
                  error: (error, stackTrace) => Text('error:$error'),
                  loading: () => const CircularProgressIndicator(),
                );
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Authority Section A'), findsOneWidget);
      expect(find.text('Authority Section B'), findsOneWidget);
      expect(find.text('Authority Section C'), findsOneWidget);

      await tester.tap(find.byKey(const Key('preview-authority-t1')));
      await tester.pump();

      expect(notifier.topologyCommits, isEmpty);
      expect(notifier.layoutCommits, isEmpty);
      expect(find.text('Authority Section B'), findsNothing);
      expect(find.text('Authority Section C'), findsOneWidget);
      expect(find.text('Authority Section A'), findsOneWidget);

      await tester.tap(find.byKey(const Key('commit-authority-topology')));
      await tester.pumpAndSettle();

      expect(notifier.topologyCommits, hasLength(1));
      expect(
        notifier
            .topologyCommits.single.expectedPreviousTopologyTransitionId?.uuid,
        authorityTopologyT0,
      );
      expect(
        notifier.topologyCommits.single.sectionStates.map(
          (section) =>
              '${section.layoutConfigSectionConfigId.uuid}:${section.order}',
        ),
        <String>['$authoritySectionC:0', '$authoritySectionA:1'],
      );
      expect(find.text('Authority Section B'), findsNothing);

      notifier.emitWatch(
        buildAuthorityHostState(
          topologyTransitionId: authorityTopologyT1,
          activeSectionIds: const <String>[
            authoritySectionC,
            authoritySectionA,
          ],
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Authority Section B'), findsNothing);

      await tester.tap(find.byKey(const Key('preview-authority-t2')));
      await tester.pump();

      expect(notifier.topologyCommits, hasLength(1));
      expect(find.text('Authority Section B'), findsOneWidget);

      await tester.tap(find.byKey(const Key('commit-authority-topology')));
      await tester.pumpAndSettle();

      expect(notifier.topologyCommits, hasLength(2));
      expect(
        notifier
            .topologyCommits.last.expectedPreviousTopologyTransitionId?.uuid,
        authorityTopologyT1,
      );
      expect(
        notifier.topologyCommits.last.sectionStates.map(
          (section) =>
              '${section.layoutConfigSectionConfigId.uuid}:${section.order}',
        ),
        <String>[
          '$authoritySectionC:0',
          '$authoritySectionB:1',
          '$authoritySectionA:2',
        ],
      );

      notifier.emitWatch(
        buildAuthorityHostState(
          topologyTransitionId: authorityTopologyT2,
          activeSectionIds: const <String>[
            authoritySectionC,
            authoritySectionB,
            authoritySectionA,
          ],
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('preview-authority-t1')));
      await tester.pump();
      expect(notifier.topologyCommits, hasLength(2));
      expect(find.text('Authority Section B'), findsNothing);

      notifier.emitWatch(
        buildAuthorityHostState(
          topologyTransitionId: authorityTopologyRemote,
          activeSectionIds: const <String>[
            authoritySectionC,
            authoritySectionB,
            authoritySectionA,
          ],
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Authority Section B'), findsOneWidget);
      expect(notifier.topologyCommits, hasLength(2));

      final handle = find.byKey(
        const Key('window-layout-resize-leading-stage'),
      );
      expect(handle, findsOneWidget);
      final gesture = await tester.startGesture(tester.getCenter(handle));
      await gesture.moveBy(const Offset(60, 0));
      await tester.pump();
      expect(notifier.layoutCommits, isEmpty);

      await gesture.up();
      await tester.pumpAndSettle();

      expect(notifier.layoutCommits, hasLength(1));
      expect(
        notifier.layoutCommits.single.topologyTransitionId?.uuid,
        authorityTopologyRemote,
      );
      expect(notifier.layoutCommits.single.sectionStates, hasLength(3));
      expect(
        notifier.layoutCommits.single.sectionStates.fold<int>(
          0,
          (sum, section) => sum + section.weightMicros,
        ),
        windowLayoutWeightMicrosTotal,
      );
    },
  );

  testWidgets(
    'two independent production Host shells converge on the same watched topology',
    (tester) async {
      tester.view.devicePixelRatio = 1.0;
      tester.view.physicalSize = const Size(1800, 900);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final initial = buildAuthorityHostState(
        topologyTransitionId: authorityTopologyT0,
        layoutTransitionId: authorityGeometryG0,
        activeSectionIds: const <String>[
          authoritySectionA,
          authoritySectionB,
          authoritySectionC,
        ],
      );
      final notifierA = _AuthorityHostStateNotifier(initial);
      final notifierB = _AuthorityHostStateNotifier(initial);

      Widget consumer(_AuthorityHostStateNotifier notifier) {
        return Expanded(
          child: ProviderScope(
            overrides: <Override>[
              interfaceHostStateProvider.overrideWith(() => notifier),
            ],
            child: Consumer(
              builder: (context, ref, _) {
                return ref.watch(interfaceHostStateProvider).when(
                      data: (value) => InterfaceHostRuntimeShell(
                        hostState: value,
                        panePackageRegistry: buildAuthorityRegistry(),
                        clientIntentIdFactory: () =>
                            'consumer-${notifier.intentSequence++}',
                      ),
                      error: (error, stackTrace) => Text('error:$error'),
                      loading: () => const CircularProgressIndicator(),
                    );
              },
            ),
          ),
        );
      }

      await tester.pumpWidget(
        MaterialApp(
          home: Row(
            children: <Widget>[consumer(notifierA), consumer(notifierB)],
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Authority Section A'), findsNWidgets(2));
      expect(find.text('Authority Section B'), findsNWidgets(2));
      expect(find.text('Authority Section C'), findsNWidgets(2));

      final watchedT1 = buildAuthorityHostState(
        topologyTransitionId: authorityTopologyT1,
        activeSectionIds: const <String>[
          authoritySectionC,
          authoritySectionA,
        ],
      );
      notifierA.emitWatch(watchedT1);
      notifierB.emitWatch(watchedT1);
      await tester.pumpAndSettle();

      expect(find.text('Authority Section A'), findsNWidgets(2));
      expect(find.text('Authority Section B'), findsNothing);
      expect(find.text('Authority Section C'), findsNWidgets(2));
      expect(notifierA.topologyCommits, isEmpty);
      expect(notifierB.topologyCommits, isEmpty);
    },
  );

  testWidgets('renders environment navigator as shell chrome outside layout', (
    tester,
  ) async {
    final registry = buildRegistry();
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceHostRuntimeShell(
          hostState: buildHostState(includeEnvironmentNavigator: true),
          panePackageRegistry: registry,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Dogfood Environment'), findsOneWidget);
    expect(find.text('Coordination'), findsOneWidget);
    expect(find.text('Conversation'), findsOneWidget);
    expect(find.byType(WindowSectionRail), findsNothing);
  });

  testWidgets(
    'remounts selected thread layout in center while navigator rail stays',
    (tester) async {
      final registry = buildRegistry();
      await tester.pumpWidget(
        MaterialApp(
          home: InterfaceHostRuntimeShell(
            hostState: buildHostState(
              includeEnvironmentNavigator: true,
              includeThreadLayout: true,
            ),
            panePackageRegistry: registry,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Dogfood Environment'), findsOneWidget);
      expect(find.text('Coordination'), findsOneWidget);
      expect(find.text('Center'), findsNothing);
      expect(find.text('Shared coordination conversation.'), findsOneWidget);
      final frame = tester.widget<WindowFullscreenSectionFrame>(
        find.byType(WindowFullscreenSectionFrame),
      );
      expect(
        frame.sections.map((section) => section.id),
        contains('conversation'),
      );
    },
  );

  testWidgets('mounts host runtime shell panes from typed window layout state',
      (
    tester,
  ) async {
    final registry = buildRegistry();
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceHostRuntimeShell(
          hostState: buildHostState(typedWindowLayout: true),
          panePackageRegistry: registry,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.byType(ChoiceChip), findsNothing);
    expect(find.text('Orchestration'), findsOneWidget);
    expect(find.text('Center'), findsOneWidget);
    expect(find.text('Inspector'), findsOneWidget);
    expect(find.text('Console'), findsOneWidget);
    expect(
      find.text(
        'mounted:workspace_representation_selector:7fbba548-0930-4c59-9ef5-0437ac4bbc9e:selector',
      ),
      findsOneWidget,
    );
    expect(
      find.text(
        'mounted:workspace:17cde6d7-0d52-54d7-b86d-a3812368dff4:flutter-test:InterfaceSdkAwareApiTransport:AwareApiClient',
      ),
      findsOneWidget,
    );
    final frame = tester.widget<WindowFullscreenSectionFrame>(
      find.byType(WindowFullscreenSectionFrame),
    );
    expect(
      frame.sections.firstWhere((section) => section.id == 'center').flex,
      2.4,
    );
  });

  testWidgets('syncs host materialized pane states into cache lifecycle', (
    tester,
  ) async {
    final store = MemoryInterfaceHostViewStateCacheStore();
    final registry = PanePackageRegistry();
    registry.registerPanePackage(
      panePackageId: UuidValue.fromString(
        '99999999-9999-4999-8999-999999999999',
      ),
      panePackageName: 'identity-admission-pane',
      paneKind: 'identity_admission',
      factory: (paneContext) => Consumer(
        builder: (context, ref, _) {
          final status = ref.watch(
            interfaceHostViewStateCacheSyncStatusProvider,
          );
          return FutureBuilder<InterfaceHostViewStateCacheEntry?>(
            future: interfaceCachedPaneViewStateForContext(ref, paneContext),
            builder: (context, snapshot) {
              final label =
                  snapshot.data?.materializedState.state['label'] ?? 'missing';
              return Text(
                'cache:${status.phase.name}:${status.result?.storedEntryCount ?? 0}:$label',
              );
            },
          );
        },
      ),
      capabilities: const runtime.PaneCapabilities(),
      displayInfo: const runtime.PaneDisplayInfo(
        paneKey: 'identity_admission',
        title: 'Identity Admission',
        description: 'Identity Admission',
      ),
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          interfaceHostViewStateCacheStoreProvider.overrideWithValue(store),
        ],
        child: MaterialApp(
          home: InterfaceHostRuntimeShell(
            hostState: buildCacheHostState(
              materializedPaneStates: <InterfaceMaterializedPaneState>[
                buildCachedState(),
              ],
            ),
            panePackageRegistry: registry,
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('cache:ready:1:Cached'), findsOneWidget);
    expect(await store.entries(namespace: 'flutter-test'), hasLength(1));

    await tester.pumpWidget(
      ProviderScope(
        overrides: <Override>[
          interfaceHostViewStateCacheStoreProvider.overrideWithValue(store),
        ],
        child: MaterialApp(
          home: InterfaceHostRuntimeShell(
            hostState: buildCacheHostState(),
            panePackageRegistry: registry,
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('cache:ready:0:missing'), findsOneWidget);
    expect(await store.entries(namespace: 'flutter-test'), isEmpty);
  });

  testWidgets('shows unavailable copy when host runtime layout is missing', (
    tester,
  ) async {
    final registry = PanePackageRegistry();
    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceHostRuntimeShell(
          hostState: InterfaceHostState(
            hostLabel: 'interface-flutter',
            namespace: 'flutter-test',
            started: true,
            transport: buildTransportState(),
          ),
          panePackageRegistry: registry,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(
      find.textContaining('has not resolved a runtime shell layout'),
      findsOneWidget,
    );
  });
}

class _RecordingLayoutTransitionHostStateNotifier
    extends InterfaceHostStateNotifier {
  _RecordingLayoutTransitionHostStateNotifier(this.hostState);

  final InterfaceHostState hostState;
  final List<
      ({
        String clientIntentId,
        UuidValue? expectedPreviousLayoutTransitionId,
        UuidValue? topologyTransitionId,
        List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates,
      })> commits = <({
    String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates,
  })>[];

  @override
  Future<InterfaceHostState> build() async => hostState;

  @override
  Future<InterfaceHostState> applyAttentionLayoutTransition({
    required String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    required List<InterfaceAttentionLayoutTransitionSectionIntent>
        sectionStates,
  }) async {
    commits.add((
      clientIntentId: clientIntentId,
      expectedPreviousLayoutTransitionId: expectedPreviousLayoutTransitionId,
      topologyTransitionId: topologyTransitionId,
      sectionStates: List<InterfaceAttentionLayoutTransitionSectionIntent>.of(
        sectionStates,
      ),
    ));
    state = AsyncData<InterfaceHostState>(hostState);
    return hostState;
  }
}

class _AuthorityHostStateNotifier extends InterfaceHostStateNotifier {
  _AuthorityHostStateNotifier(this.hostState);

  InterfaceHostState hostState;
  int intentSequence = 1;
  final List<
      ({
        String clientIntentId,
        UuidValue? expectedPreviousTopologyTransitionId,
        List<
            InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates,
      })> topologyCommits = <({
    String clientIntentId,
    UuidValue? expectedPreviousTopologyTransitionId,
    List<InterfaceAttentionLayoutTopologyTransitionSectionIntent> sectionStates,
  })>[];
  final List<
      ({
        String clientIntentId,
        UuidValue? expectedPreviousLayoutTransitionId,
        UuidValue? topologyTransitionId,
        List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates,
      })> layoutCommits = <({
    String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    List<InterfaceAttentionLayoutTransitionSectionIntent> sectionStates,
  })>[];

  @override
  Future<InterfaceHostState> build() async => hostState;

  void emitWatch(InterfaceHostState next) {
    hostState = next;
    state = AsyncData<InterfaceHostState>(next);
  }

  @override
  Future<InterfaceHostState> applyAttentionLayoutTopologyTransition({
    required String clientIntentId,
    UuidValue? expectedPreviousTopologyTransitionId,
    required List<InterfaceAttentionLayoutTopologyTransitionSectionIntent>
        sectionStates,
  }) async {
    topologyCommits.add((
      clientIntentId: clientIntentId,
      expectedPreviousTopologyTransitionId:
          expectedPreviousTopologyTransitionId,
      sectionStates:
          List<InterfaceAttentionLayoutTopologyTransitionSectionIntent>.of(
        sectionStates,
      ),
    ));
    return hostState;
  }

  @override
  Future<InterfaceHostState> applyAttentionLayoutTransition({
    required String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    required List<InterfaceAttentionLayoutTransitionSectionIntent>
        sectionStates,
  }) async {
    layoutCommits.add((
      clientIntentId: clientIntentId,
      expectedPreviousLayoutTransitionId: expectedPreviousLayoutTransitionId,
      topologyTransitionId: topologyTransitionId,
      sectionStates: List<InterfaceAttentionLayoutTransitionSectionIntent>.of(
        sectionStates,
      ),
    ));
    return hostState;
  }
}
