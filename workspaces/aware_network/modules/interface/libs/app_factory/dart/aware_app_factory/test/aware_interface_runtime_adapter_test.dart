import 'package:aware_app_factory/aware_app_factory.dart';
import 'package:aware_pane/aware_pane.dart' as pane_model;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid_value.dart';

void main() {
  const adapter = AwareInterfaceRuntimeAdapter();

  test('derives sections and pane package identity from runtime metadata', () {
    final runtime = _testRuntime();

    final sections = adapter.sectionsForLayout(
      runtime,
      layoutKey: 'control',
      policy: const AwareAppSectionPolicy(
        layouts: {
          'control': [
            AwareAppSectionSpec(
              sectionKey: 'primary',
              region: WindowFullscreenSectionRegion.stage,
              order: 0,
              title: 'Primary',
            ),
          ],
        },
      ),
    );
    final panes = adapter.resolvedPanesForLayout(
      runtime,
      windowKey: 'main',
      layoutKey: 'control',
    );

    expect(sections, hasLength(1));
    expect(sections.single.sectionKey, 'primary');
    expect(panes, hasLength(1));
    expect(panes.single.paneKind, 'proof');
    expect(panes.single.panePackageName, 'proof-pane');
    expect(panes.single.panePackageId, stablePanePackageId(name: 'proof-pane'));
    expect(panes.single.viewRef, 'proof.view');
    expect(panes.single.projectionViewKey, 'proof.view.v1');
  });

  test(
    'default route is a committed screen and runtimes are package-only',
    () {
      final manifest = AwareAppLaunchManifest(
        appPackage: _appPackage,
        defaultScreenKey: 'control',
        composition: const AwareAppComposition(
          appId: 'aware-proof',
          displayName: 'Aware Proof',
          controlPolicy: AwareAppControlPolicy(
            defaultScreenKey: 'control',
            admittedScreenKey: 'home',
          ),
        ),
        catalog: AwareAppRuntimeCatalog(
          registrations: [
            AwareInterfaceRuntimeRegistration(
              interfacePackageId: 'control-package',
              interfacePackageName: 'aware-control-interface',
              buildRuntime: _testControlRuntime,
            ),
            AwareInterfaceRuntimeRegistration(
              interfacePackageId: 'home-package',
              interfacePackageName: 'home-story-aware-app-interface',
              buildRuntime: _testRuntime,
            ),
          ],
        ),
        committedScreens: _controlAndHomeScreens,
      );

      expect(manifest.validate(), isEmpty);
      expect(manifest.defaultScreenKey, 'control');
      expect(
        manifest.composition.controlPolicy.admittedScreenKey,
        'home',
      );
      expect(
        manifest.catalog.interfacePackageNames(),
        ['aware-control-interface', 'home-story-aware-app-interface'],
      );
    },
  );

  test('validation blocks an uncommitted admitted screen', () {
    final manifest = AwareAppLaunchManifest(
      appPackage: _appPackage,
      defaultScreenKey: 'home',
      composition: const AwareAppComposition(
        appId: 'aware-proof',
        displayName: 'Aware Proof',
        controlPolicy: AwareAppControlPolicy(
          defaultScreenKey: 'home',
          admittedScreenKey: 'missing',
        ),
      ),
      catalog: AwareAppRuntimeCatalog(
        registrations: [
          AwareInterfaceRuntimeRegistration(
            interfacePackageId: 'home-package',
            interfacePackageName: 'home-story-aware-app-interface',
            buildRuntime: _testRuntime,
          ),
        ],
      ),
      committedScreens: const [_homeScreen],
    );

    expect(
      manifest.validate(),
      contains('control policy admitted screen is not committed'),
    );
  });

  test('session authority is blocked without host state', () {
    final authority = AwareAppSessionAuthority.fromHostState(
      null,
      appPackage: _appPackage,
      screen: _homeScreen,
    );

    expect(authority.canMountCommittedScreen, isFalse);
    expect(authority.screenAccepted, isFalse);
    expect(authority.blockedReason, contains('App screen authority'));
  });

  test('session authority is blocked by rejected App screen', () {
    final authority = AwareAppSessionAuthority.fromHostState(
      _hostState(appScreenAccepted: false),
      appPackage: _appPackage,
      screen: _homeScreen,
    );

    expect(authority.canMountCommittedScreen, isFalse);
    expect(authority.screenAccepted, isFalse);
    expect(authority.blockedReason, contains('committed App screen'));
  });

  test('session authority accepts exact committed App screen evidence', () {
    final authority = AwareAppSessionAuthority.fromHostState(
      _hostState(appScreenAccepted: true),
      appPackage: _appPackage,
      screen: _homeScreen,
    );

    expect(authority.canMountCommittedScreen, isTrue);
    expect(authority.screenAccepted, isTrue);
    expect(authority.committedEvidenceMatches, isTrue);
    expect(authority.experienceLensReady, isFalse);
    expect(authority.blockedReason, isNull);
  });

  test('session authority rejects a different committed App revision', () {
    final authority = AwareAppSessionAuthority.fromHostState(
      _hostState(
        appScreenAccepted: true,
        appPackageCommitId: '99999999-9999-4999-8999-999999999999',
      ),
      appPackage: _appPackage,
      screen: _homeScreen,
    );

    expect(authority.canMountCommittedScreen, isFalse);
    expect(authority.screenAccepted, isTrue);
    expect(authority.committedEvidenceMatches, isFalse);
    expect(authority.blockedReason, contains('different App package revision'));
  });

  test(
    'control admission dispatch enters target after canonical action',
    () async {
      final order = <String>[];
      Map<String, dynamic>? capturedEvidence;

      await dispatchAwareAppRenderSpecAction(
        invocation: _actionInvocation('admit_identity'),
        appPackage: _appPackage,
        committedScreen: _homeScreen,
        dispatchCanonicalAction: (invocation) async {
          order.add('canonical:${invocation.actionKey}');
        },
        enterCommittedScreen: (appPackage, screen, invocation, evidence) async {
          order.add('enter:${screen.screenKey}:${invocation.actionKey}');
          capturedEvidence = evidence;
        },
      );

      expect(order, ['canonical:admit_identity', 'enter:home:admit_identity']);
      expect(
        capturedEvidence?['aware_app_package'],
        containsPair('app_package_id', _appPackage.appPackageId),
      );
      expect(
        capturedEvidence?['aware_app_screen'],
        containsPair(
          'app_config_screen_config_id',
          _homeScreen.appConfigScreenConfigId,
        ),
      );
      expect(capturedEvidence?['control_action_key'], 'admit_identity');
    },
  );

  test('non-admission render actions do not enter target', () async {
    final order = <String>[];

    await dispatchAwareAppRenderSpecAction(
      invocation: _actionInvocation('refresh_territory'),
      appPackage: _appPackage,
      committedScreen: _homeScreen,
      dispatchCanonicalAction: (invocation) async {
        order.add('canonical:${invocation.actionKey}');
      },
      enterCommittedScreen: (appPackage, screen, invocation, evidence) async {
        order.add('enter:${screen.screenKey}:${invocation.actionKey}');
      },
    );

    expect(order, ['canonical:refresh_territory']);
  });

  testWidgets('factory mounts accepted screen through Interface Host shell', (
    tester,
  ) async {
    final manifest = AwareAppLaunchManifest(
      appPackage: _appPackage,
      defaultScreenKey: 'proof',
      composition: const AwareAppComposition(
        appId: 'aware-proof',
        displayName: 'Aware Proof',
        controlPolicy: AwareAppControlPolicy(defaultScreenKey: 'proof'),
      ),
      catalog: AwareAppRuntimeCatalog(
        registrations: [
          AwareInterfaceRuntimeRegistration(
            interfacePackageId: 'proof-package',
            interfacePackageName: 'proof-interface',
            buildRuntime: _testRuntime,
          ),
        ],
      ),
      committedScreens: const [_proofScreen],
    );

    await tester.pumpWidget(
      AwareAppFactoryRoot(
        manifest: manifest,
        providerOverrides: [
          interfaceHostStateProvider.overrideWith(
            () => _StaticInterfaceHostStateNotifier(
              _hostState(
                appScreenAccepted: true,
                screen: _proofScreen,
                interfacePackageName: 'proof-interface',
                layoutKey: 'control',
                sectionKey: 'primary',
                resolvedPanes: <InterfaceResolvedPaneDescriptor>[
                  _proofResolvedPane(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Aware Proof'), findsOneWidget);
    expect(find.text('proof-pane:proof:primary'), findsOneWidget);
  });

  testWidgets('factory enters the default committed screen through Host', (
    tester,
  ) async {
    final notifier = _RecordingInterfaceHostStateNotifier(
      initialState: _hostState(),
      acceptedState: _hostState(
        appScreenAccepted: true,
        screen: _proofScreen,
        interfacePackageName: 'proof-interface',
        layoutKey: 'control',
        sectionKey: 'primary',
        resolvedPanes: <InterfaceResolvedPaneDescriptor>[
          _proofResolvedPane(),
        ],
      ),
    );
    final manifest = AwareAppLaunchManifest(
      appPackage: _appPackage,
      defaultScreenKey: 'proof',
      composition: const AwareAppComposition(
        appId: 'aware-proof',
        displayName: 'Aware Proof',
        controlPolicy: AwareAppControlPolicy(defaultScreenKey: 'proof'),
      ),
      catalog: AwareAppRuntimeCatalog(
        registrations: [
          AwareInterfaceRuntimeRegistration(
            interfacePackageId: 'proof-package',
            interfacePackageName: 'proof-interface',
            buildRuntime: _testRuntime,
          ),
        ],
      ),
      committedScreens: const [_proofScreen],
    );

    await tester.pumpWidget(
      AwareAppFactoryRoot(
        manifest: manifest,
        providerOverrides: [
          interfaceHostStateProvider.overrideWith(() => notifier),
        ],
      ),
    );
    await tester.pumpAndSettle();

    expect(notifier.enteredScreenConfigIds, [
      _proofScreen.appConfigScreenConfigId,
    ]);
    expect(find.text('proof-pane:proof:primary'), findsOneWidget);
  });

  testWidgets('factory fails closed for a mismatched committed screen', (
    tester,
  ) async {
    final hostState = _hostState(
      appScreenAccepted: true,
      screen: _homeScreen,
      interfacePackageName: 'proof-interface',
      layoutKey: 'control',
      sectionKey: 'primary',
    );

    await tester.pumpWidget(
      AwareAppFactoryRoot(
        manifest: AwareAppLaunchManifest(
          appPackage: _appPackage,
          defaultScreenKey: 'proof',
          composition: const AwareAppComposition(
            appId: 'aware-proof',
            displayName: 'Aware Proof',
            controlPolicy: AwareAppControlPolicy(defaultScreenKey: 'proof'),
          ),
          catalog: AwareAppRuntimeCatalog(
            registrations: [
              AwareInterfaceRuntimeRegistration(
                interfacePackageId: 'proof-package',
                interfacePackageName: 'proof-interface',
                buildRuntime: _testRuntime,
              ),
            ],
          ),
          committedScreens: const [_proofScreen],
        ),
        providerOverrides: [
          interfaceHostStateProvider.overrideWith(
            () => _StaticInterfaceHostStateNotifier(hostState),
          ),
        ],
      ),
    );
    await tester.pump();

    expect(find.text('App screen unavailable'), findsOneWidget);
    expect(find.text('proof-pane:proof:primary'), findsNothing);
  });

  testWidgets('factory renders render-spec fallback without host pane state', (
    tester,
  ) async {
    await tester.pumpWidget(
      AwareAppFactoryRoot(
        manifest: _renderSpecManifest(),
        providerOverrides: [
          interfaceHostStateProvider.overrideWith(
            () => _StaticInterfaceHostStateNotifier(
              _hostState(
                appScreenAccepted: true,
                resolvedPanes: <InterfaceResolvedPaneDescriptor>[
                  _homeResolvedPane(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.text('Home state is waiting for a service view snapshot.'),
      findsOneWidget,
    );
  });

  testWidgets('factory forwards host materialized states to render specs', (
    tester,
  ) async {
    await tester.pumpWidget(
      AwareAppFactoryRoot(
        manifest: _renderSpecManifest(),
        providerOverrides: [
          interfaceHostStateProvider.overrideWith(
            () => _StaticInterfaceHostStateNotifier(
              _hostState(
                appScreenAccepted: true,
                materializedPaneStates: <InterfaceMaterializedPaneState>[
                  _homeOverviewMaterializedState(
                    summary: 'Live Home snapshot from Interface Host.',
                  ),
                ],
                resolvedPanes: <InterfaceResolvedPaneDescriptor>[
                  _homeResolvedPane(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.text('Live Home snapshot from Interface Host.'),
      findsOneWidget,
    );
    expect(
      find.text('Home state is waiting for a service view snapshot.'),
      findsNothing,
    );
  });
}

const _appPackage = AwareAppPackageEvidence(
  packageName: 'aware-home-app',
  appPackageId: '11111111-1111-4111-8111-111111111111',
  branchId: '22222222-2222-4222-8222-222222222222',
  objectInstanceGraphCommitId: '33333333-3333-4333-8333-333333333333',
);

const _controlScreen = AwareAppCommittedScreen(
  appConfigScreenConfigId: '44444444-4444-4444-8444-444444444444',
  screenKey: 'control',
  projectionExperienceId: '55555555-5555-4555-8555-555555555555',
  projectionExperienceLayoutGraphBindingId:
      '66666666-6666-4666-8666-666666666666',
);

const _homeScreen = AwareAppCommittedScreen(
  appConfigScreenConfigId: '77777777-7777-4777-8777-777777777777',
  screenKey: 'home',
  projectionExperienceId: '88888888-8888-4888-8888-888888888888',
  projectionExperienceLayoutGraphBindingId:
      '99999999-9999-4999-8999-999999999999',
);

const _proofScreen = AwareAppCommittedScreen(
  appConfigScreenConfigId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  screenKey: 'proof',
  projectionExperienceId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
  projectionExperienceLayoutGraphBindingId:
      'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
);

const _controlAndHomeScreens = [_controlScreen, _homeScreen];

PaneRenderActionInvocation _actionInvocation(String actionKey) {
  return PaneRenderActionInvocation(
    paneContext: PaneContext(paneId: 'control', kind: 'control'),
    actionBinding: PaneActionBinding(
      bindingKey: actionKey,
      event: kPaneRenderActionEventActivate,
      actionKey: actionKey,
      actionKind: kPaneRenderActionKindViewAction,
    ),
    payload: const {'display_name': 'Luis'},
  );
}

InterfaceHostState _hostState({
  bool? appScreenAccepted,
  String appPackageCommitId = '33333333-3333-4333-8333-333333333333',
  AwareAppCommittedScreen screen = _homeScreen,
  String interfacePackageName = 'home-proof-interface',
  String layoutKey = 'configuration_map',
  String sectionKey = 'workspace',
  List<InterfaceMaterializedPaneState> materializedPaneStates = const [],
  List<InterfaceResolvedPaneDescriptor> resolvedPanes = const [],
}) {
  return InterfaceHostState(
    hostLabel: 'test-host',
    namespace: 'test',
    started: true,
    transport: InterfaceTransportState(
      available: true,
      registered: true,
      authenticated: true,
    ),
    appScreen: appScreenAccepted == null
        ? null
        : InterfaceAppScreenState(
            status: appScreenAccepted ? 'accepted' : 'blocked',
            accepted: appScreenAccepted,
            appPackageId: UuidValue.fromString(_appPackage.appPackageId),
            appPackageBranchId: UuidValue.fromString(_appPackage.branchId),
            appPackageObjectInstanceGraphCommitId: UuidValue.fromString(
              appPackageCommitId,
            ),
            appConfigScreenConfigId: UuidValue.fromString(
              screen.appConfigScreenConfigId,
            ),
            blockers: appScreenAccepted ? const [] : const ['identity missing'],
            evidence: const <String, dynamic>{},
          ),
    runtime: InterfaceRuntimeState(
      backend: _testBackendState(),
      resolvedView: InterfaceResolvedView(
        experienceKey: 'test-experience',
        interfacePackageName: interfacePackageName,
        projectionViewId: 'test.view.v1',
        hostPayload: const <String, dynamic>{},
      ),
      windowLayout: InterfaceWindowLayoutState(
        sourceKind: 'committed_oig',
        windowKey: 'main',
        layoutKey: layoutKey,
        frameMode: 'grid',
        stale: false,
        sections: [
          InterfaceWindowLayoutSectionState(
            sectionKey: sectionKey,
            order: 0,
            flex: 1,
            isVisible: true,
            isCollapsed: false,
          ),
        ],
      ),
      resolvedPanes: resolvedPanes,
      materializedPaneStates: materializedPaneStates,
    ),
  );
}

InterfaceResolvedPaneDescriptor _proofResolvedPane() {
  return InterfaceResolvedPaneDescriptor(
    windowKey: 'main',
    layoutKey: 'control',
    sectionKey: 'primary',
    paneKind: 'proof',
    panePackageId: stablePanePackageId(name: 'proof-pane'),
    panePackageName: 'proof-pane',
    stateSourceKind: 'section_focus_scope_lane',
  );
}

InterfaceResolvedPaneDescriptor _homeResolvedPane() {
  return InterfaceResolvedPaneDescriptor(
    windowKey: 'main',
    layoutKey: 'configuration_map',
    sectionKey: 'workspace',
    paneKind: 'home',
    projectionExperienceViewId: UuidValue.fromString(
      '174b19f6-894e-5e4e-b452-149f67fb9f8e',
    ),
    projectionViewId: 'overview.home',
    viewRef: 'home_story.overview.home',
    projectionViewKey: 'overview.home',
    stateSourceKind: 'experience_view_state',
  );
}

InterfacePackageRuntime _testControlRuntime() {
  return InterfacePackageRuntime(
    interfacePackageId: 'control-package',
    interfacePackageName: 'aware-control-interface',
    panePackageRegistry: PanePackageRegistry(),
    layouts: const [
      InterfacePackageRuntimeLayout(
        layoutConfigId: 'control-layout',
        layoutKey: 'control',
        label: 'Control',
        isDefault: true,
      ),
    ],
  );
}

InterfacePackageRuntime _testRuntime() {
  final registry = PanePackageRegistry()
    ..registerPanePackage(
      panePackageId: stablePanePackageId(name: 'proof-pane'),
      panePackageName: 'proof-pane',
      paneKind: 'proof',
      capabilities: const pane_model.PaneCapabilities(),
      displayInfo: const pane_model.PaneDisplayInfo(
        paneKey: 'proof',
        title: 'Proof',
        description: 'Proof pane',
      ),
      factory: (context) => Text(
        'proof-pane:${context.kind}:${context.parameters['sectionKey']}',
      ),
    );

  return InterfacePackageRuntime(
    interfacePackageId: 'proof-package',
    interfacePackageName: 'proof-interface',
    panePackageRegistry: registry,
    layouts: const [
      InterfacePackageRuntimeLayout(
        layoutConfigId: 'proof-layout',
        layoutKey: 'control',
        label: 'Control',
        isDefault: true,
      ),
    ],
    sectionRepresentations: const [
      InterfacePackageRuntimeSectionRepresentation(
        representationId: 'proof-representation',
        windowKey: 'main',
        layoutKey: 'control',
        sectionKey: 'primary',
        paneName: 'proof_pane',
        paneKind: 'proof',
        label: 'Proof',
        observableId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        viewRef: 'proof.view',
        projectionViewKey: 'proof.view.v1',
      ),
    ],
  );
}

AwareAppLaunchManifest _renderSpecManifest() {
  return AwareAppLaunchManifest(
    appPackage: _appPackage,
    defaultScreenKey: 'home',
    composition: const AwareAppComposition(
      appId: 'aware-home-proof',
      displayName: 'Aware Home Proof',
      controlPolicy: AwareAppControlPolicy(defaultScreenKey: 'home'),
    ),
    catalog: AwareAppRuntimeCatalog(
      registrations: [
        AwareInterfaceRuntimeRegistration(
          interfacePackageId: 'home-proof-package',
          interfacePackageName: 'home-proof-interface',
          buildRuntime: _testRenderSpecRuntime,
        ),
      ],
    ),
    committedScreens: const [_homeScreen],
  );
}

InterfacePackageRuntime _testRenderSpecRuntime() {
  return InterfacePackageRuntime(
    interfacePackageId: 'home-proof-package',
    interfacePackageName: 'home-proof-interface',
    panePackageRegistry: PanePackageRegistry(),
    layouts: const [
      InterfacePackageRuntimeLayout(
        layoutConfigId: 'configuration-map-layout',
        layoutKey: 'configuration_map',
        label: 'Configuration Map',
        isDefault: true,
      ),
    ],
    sectionRepresentations: const [
      InterfacePackageRuntimeSectionRepresentation(
        representationId: 'home-overview-representation',
        windowKey: 'main',
        layoutKey: 'configuration_map',
        sectionKey: 'workspace',
        paneName: 'home_overview',
        paneKind: 'home',
        label: 'Overview',
        observableId: '174b19f6-894e-5e4e-b452-149f67fb9f8e',
        viewRef: 'home_story.overview.home',
        projectionViewKey: 'overview.home',
      ),
    ],
    renderSpecs: const <PaneRenderSpec>[
      PaneRenderSpec(
        specId: 'home-overview-render-spec-v0',
        name: 'home_overview_default',
        specVersion: '0.1.0',
        paneKind: 'home',
        viewRef: 'home_story.overview.home',
        projectionViewKey: 'overview.home',
        rootNodeKey: 'root',
        nodes: <PaneRenderNode>[
          PaneRenderNode(
            nodeKey: 'root',
            nodeKind: kPaneRenderNodeKindColumn,
            semanticRole: 'pane',
          ),
          PaneRenderNode(
            nodeKey: 'summary',
            parentNodeKey: 'root',
            nodeKind: kPaneRenderNodeKindField,
            semanticRole: 'paragraph',
            label: 'Summary',
            stateBindings: <PaneStateBinding>[
              PaneStateBinding(
                bindingKey: 'summary_text',
                targetProperty: kPaneRenderStateTargetText,
                jsonPath: r'$.summary',
                transform: kPaneRenderStateTransformText,
                fallbackValue:
                    'Home state is waiting for a service view snapshot.',
              ),
            ],
          ),
        ],
      ),
    ],
  );
}

InterfaceBackendState _testBackendState() {
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

InterfaceMaterializedPaneState _homeOverviewMaterializedState({
  required String summary,
}) {
  return InterfaceMaterializedPaneState(
    paneStateKey: 'main:configuration_map:workspace:home::',
    windowKey: 'main',
    layoutKey: 'configuration_map',
    sectionKey: 'workspace',
    paneKind: 'home',
    projectionExperienceViewId: UuidValue.fromString(
      '174b19f6-894e-5e4e-b452-149f67fb9f8e',
    ),
    projectionViewId: 'overview.home',
    status: 'materialized',
    state: <String, dynamic>{'summary': summary},
    provenance: const <String, dynamic>{
      'source': 'interface_host_runtime_state',
    },
  );
}

class _StaticInterfaceHostStateNotifier extends InterfaceHostStateNotifier {
  _StaticInterfaceHostStateNotifier(this._hostState);

  final InterfaceHostState _hostState;

  @override
  Future<InterfaceHostState> build() async {
    return _hostState;
  }
}

class _RecordingInterfaceHostStateNotifier extends InterfaceHostStateNotifier {
  _RecordingInterfaceHostStateNotifier({
    required this.initialState,
    required this.acceptedState,
  });

  final InterfaceHostState initialState;
  final InterfaceHostState acceptedState;
  final List<String> enteredScreenConfigIds = <String>[];

  @override
  Future<InterfaceHostState> build() async => initialState;

  @override
  Future<InterfaceHostState> enterAppScreen({
    required UuidValue appPackageId,
    required UuidValue appPackageBranchId,
    required UuidValue appPackageObjectInstanceGraphCommitId,
    required UuidValue appConfigScreenConfigId,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    enteredScreenConfigIds.add(appConfigScreenConfigId.uuid);
    state = AsyncData<InterfaceHostState>(acceptedState);
    return acceptedState;
  }
}
