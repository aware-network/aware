import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid_value.dart';

void main() {
  test('API-delivered dynamic render specs override static package specs', () {
    final registry = InterfacePackageRuntimeRegistry();
    registry.register(
      InterfacePackageRuntime(
        interfacePackageId: 'aware-control-interface',
        interfacePackageName: 'aware-control-interface',
        panePackageRegistry: PanePackageRegistry(),
        experienceKeys: const <String>['aware.control'],
        renderSpecs: <PaneRenderSpec>[
          _textRenderSpec('static bundle render spec'),
        ],
      ),
    );

    final runtime = resolveInterfacePackageRuntimeForHostState(
      registry: registry,
      hostState: InterfaceHostState(
        hostLabel: 'interface-flutter-test',
        namespace: 'flutter-test',
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware.control',
            interfacePackageName: 'aware-control-interface',
            hostPayload: const <String, dynamic>{},
          ),
          dynamicPaneRenderSpecs: <InterfaceRuntimePaneRenderSpecState>[
            InterfaceRuntimePaneRenderSpecState(
              sourceKind: 'committed_oig',
              branchId: UuidValue.fromString(
                '11111111-1111-4111-8111-111111111111',
              ),
              projectionHash: 'identity-hash',
              lastCommitId: UuidValue.fromString(
                '22222222-2222-4222-8222-222222222222',
              ),
              objectInstanceGraphCommitId: UuidValue.fromString(
                '33333333-3333-4333-8333-333333333333',
              ),
              paneRenderSpecId: UuidValue.fromString(
                '44444444-4444-4444-8444-444444444444',
              ),
              paneConfigId: UuidValue.fromString(
                '55555555-5555-4555-8555-555555555555',
              ),
              renderSpecContentHashSha256: 'render-spec-hash',
              payload: _textRenderSpecPayload('committed OIG render spec'),
            ),
          ],
        ),
      ),
    );

    expect(runtime, isNotNull);
    expect(runtime!.renderSpecs, hasLength(1));
    expect(
      runtime.renderSpecs.single.nodes.single.text,
      'committed OIG render spec',
    );
  });

  test('builds data-only package runtime from Interface DTO state', () {
    final runtime = InterfacePackageRuntime.fromRuntimePackageState(
      InterfaceRuntimePackageState(
        sourceKind: 'interface_api',
        interfacePackageId: UuidValue.fromString(
          'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        ),
        interfacePackageName: 'customer-interface',
        experienceKeys: const <String>['customer_experience'],
        layouts: <InterfaceRuntimeLayoutState>[
          InterfaceRuntimeLayoutState(
            layoutConfigId: UuidValue.fromString(
              'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
            ),
            layoutKey: 'customer_layout',
            label: 'Customer Layout',
            isDefault: true,
            isActive: true,
          ),
        ],
        sectionRepresentations: <InterfaceRuntimeSectionRepresentationState>[
          InterfaceRuntimeSectionRepresentationState(
            representationId: UuidValue.fromString(
              'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
            ),
            windowKey: 'main',
            layoutKey: 'customer_layout',
            sectionKey: 'workspace',
            paneName: 'customer_admission',
            paneKind: 'identity_admission',
            label: 'Customer Admission',
            observableId: UuidValue.fromString(
              'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
            ),
            viewRef: 'aware_control_identity.identity.admission.v1',
            projectionViewKey: 'identity.admission.v1',
            isActive: true,
          ),
        ],
        apiPackages: <InterfaceRuntimePackageApiPackageState>[
          InterfaceRuntimePackageApiPackageState(
            apiPackageId: UuidValue.fromString(
              'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
            ),
            apiPackageName: 'customer-service-api',
          ),
        ],
        apis: <InterfaceRuntimePackageApiState>[
          InterfaceRuntimePackageApiState(
            interfaceName: 'customer-interface',
            interfaceConfigId: UuidValue.fromString(
              'ffffffff-ffff-4fff-8fff-ffffffffffff',
            ),
            interfaceConfigApiId: UuidValue.fromString(
              '11111111-1111-4111-8111-111111111111',
            ),
            apiId: UuidValue.fromString('22222222-2222-4222-8222-222222222222'),
            apiRef: 'identity',
          ),
        ],
        dynamicPaneRenderSpecs: <InterfaceRuntimePaneRenderSpecState>[
          InterfaceRuntimePaneRenderSpecState(
            sourceKind: 'committed_oig',
            paneRenderSpecId: UuidValue.fromString(
              '33333333-3333-4333-8333-333333333333',
            ),
            paneConfigId: UuidValue.fromString(
              '44444444-4444-4444-8444-444444444444',
            ),
            payload: _textRenderSpecPayload('data-only render spec'),
          ),
        ],
        renderComponents: <InterfaceRuntimePackageRenderComponentState>[
          InterfaceRuntimePackageRenderComponentState(
            componentRef: 'aware.content.markdown_viewer',
            displayName: 'Markdown viewer',
          ),
        ],
      ),
    );

    expect(runtime.interfacePackageName, 'customer-interface');
    expect(runtime.experienceKeys, const <String>['customer_experience']);
    expect(runtime.layouts.single.layoutKey, 'customer_layout');
    expect(
      runtime.sectionRepresentations.single.paneKind,
      'identity_admission',
    );
    expect(runtime.apiPackages.single.apiPackageName, 'customer-service-api');
    expect(runtime.apis.single.apiRef, 'identity');
    expect(
      runtime.renderSpecs.single.nodes.single.text,
      'data-only render spec',
    );
    expect(runtime.panePackageRegistry.registeredPanePackageIds(), isEmpty);

    final registry = InterfacePackageRuntimeRegistry()..register(runtime);
    expect(
      registry.resolve(interfacePackageName: 'customer-interface'),
      same(runtime),
    );
    expect(
      registry.resolve(experienceKey: 'customer_experience'),
      same(runtime),
    );
  });

  test('host-carried data-only runtime satisfies package readiness', () {
    final packageId = UuidValue.fromString(
      'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    );
    final hostState = InterfaceHostState(
      hostLabel: 'interface-flutter-test',
      namespace: 'flutter-test',
      started: true,
      transport: _testTransportState(),
      runtime: InterfaceRuntimeState(
        backend: _testBackendState(),
        resolvedView: InterfaceResolvedView(
          experienceKey: 'customer_experience',
          interfacePackageId: packageId,
          interfacePackageName: 'customer-interface',
          hostPayload: const <String, dynamic>{},
        ),
        interfacePackageRuntime: InterfaceRuntimePackageState(
          sourceKind: 'interface_api',
          interfacePackageId: packageId,
          interfacePackageName: 'customer-interface',
          experienceKeys: const <String>['customer_experience'],
          dynamicPaneRenderSpecs: <InterfaceRuntimePaneRenderSpecState>[
            InterfaceRuntimePaneRenderSpecState(
              sourceKind: 'committed_oig',
              paneRenderSpecId: UuidValue.fromString(
                '33333333-3333-4333-8333-333333333333',
              ),
              paneConfigId: UuidValue.fromString(
                '44444444-4444-4444-8444-444444444444',
              ),
              payload: _textRenderSpecPayload('host-carried render spec'),
            ),
          ],
        ),
      ),
    );

    final runtime = resolveInterfacePackageRuntimeForHostState(
      registry: InterfacePackageRuntimeRegistry(),
      hostState: hostState,
    );
    expect(runtime, isNotNull);
    expect(runtime!.interfacePackageName, 'customer-interface');
    expect(runtime.sourceKind, 'interface_api');
    expect(
      runtime.renderSpecs.single.nodes.single.text,
      'host-carried render spec',
    );

    final readiness = resolveInterfacePackageRuntimeReadiness(
      registry: InterfacePackageRuntimeRegistry(),
      hostState: hostState,
    );
    expect(readiness.ready, isTrue);
    expect(readiness.blocksRuntimeShell, isFalse);
    expect(
      readiness.interfacePackageRuntime?.interfacePackageName,
      'customer-interface',
    );
  });

  test('host-carried data-only runtime wins over static Dart registry', () {
    final packageId = UuidValue.fromString(
      'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    );
    final registry = InterfacePackageRuntimeRegistry()
      ..register(
        InterfacePackageRuntime(
          interfacePackageId: packageId.uuid,
          interfacePackageName: 'aware-control-interface',
          panePackageRegistry: PanePackageRegistry(),
          experienceKeys: const <String>['aware_control'],
          renderSpecs: <PaneRenderSpec>[
            _textRenderSpec('static accelerator render spec'),
          ],
        ),
      );
    final hostState = InterfaceHostState(
      hostLabel: 'interface-flutter-test',
      namespace: 'flutter-test',
      started: true,
      transport: _testTransportState(),
      runtime: InterfaceRuntimeState(
        backend: _testBackendState(),
        resolvedView: InterfaceResolvedView(
          experienceKey: 'aware.interface.bootstrap',
          interfacePackageId: packageId,
          interfacePackageName: 'aware-control-interface',
          hostPayload: const <String, dynamic>{},
        ),
        interfacePackageRuntime: InterfaceRuntimePackageState(
          sourceKind: 'interface_host_config_bundle',
          interfacePackageId: packageId,
          interfacePackageName: 'aware-control-interface',
          experienceKeys: const <String>['aware.interface.bootstrap'],
        ),
      ),
    );

    final runtime = resolveInterfacePackageRuntimeForHostState(
      registry: registry,
      hostState: hostState,
    );

    expect(runtime, isNotNull);
    expect(runtime!.sourceKind, 'interface_host_config_bundle');
    expect(runtime.experienceKeys, const <String>[
      'aware.interface.bootstrap',
      'aware_control',
    ]);
    expect(
      runtime.renderSpecs.single.nodes.single.text,
      'static accelerator render spec',
    );

    final readiness = resolveInterfacePackageRuntimeReadiness(
      registry: registry,
      hostState: hostState,
    );
    expect(readiness.ready, isTrue);
    expect(readiness.title, 'Interface Runtime Ready');
    expect(readiness.message, contains('data-only runtime'));
    expect(
      readiness.interfacePackageRuntime?.sourceKind,
      'interface_host_config_bundle',
    );
  });

  test('host surface drift is diagnostic and does not block shell entry', () {
    final registry = InterfacePackageRuntimeRegistry();
    registry.register(
      InterfacePackageRuntime(
        interfacePackageId: 'aware-control-interface',
        interfacePackageName: 'aware-control-interface',
        panePackageRegistry: PanePackageRegistry(),
        experienceKeys: const <String>['aware.control'],
        renderSpecs: <PaneRenderSpec>[
          _textRenderSpec('committed OIG render spec'),
        ],
      ),
    );

    final readiness = resolveInterfacePackageRuntimeReadiness(
      registry: registry,
      hostState: InterfaceHostState(
        hostLabel: 'interface-flutter-test',
        namespace: 'flutter-test',
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware.control',
            interfacePackageName: 'aware-control-interface',
            hostPayload: const <String, dynamic>{},
          ),
          sectionRepresentations: <InterfaceRuntimeSectionRepresentationState>[
            InterfaceRuntimeSectionRepresentationState(
              representationId: UuidValue.fromString(
                '873617f9-7681-5bd0-9fce-2706d410d648',
              ),
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'inspector',
              paneName: 'network_territory',
              paneKind: 'network_territory',
              label: 'Network',
              observableId: UuidValue.fromString(
                'bc476991-5438-5b1c-bca9-079412f3e929',
              ),
              viewRef: 'aware_network.territory.discovery.v1',
              projectionViewKey: 'territory.discovery.v1',
              isActive: true,
            ),
          ],
          resolvedPanes: <InterfaceResolvedPaneDescriptor>[
            InterfaceResolvedPaneDescriptor(
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'inspector',
              paneKind: 'network_territory',
              panePackageId: UuidValue.fromString(
                '4df05965-63a7-5a27-a54f-cf479cac2545',
              ),
              panePackageName: 'aware-network-territory-pane',
              viewRef: 'aware_network.territory.discovery.v1',
              projectionViewKey: 'territory.discovery.v1',
              stateSourceKind: 'interface-host',
            ),
          ],
        ),
      ),
    );

    expect(readiness.ready, isTrue);
    expect(readiness.blocksRuntimeShell, isFalse);
    expect(
      readiness.issues,
      contains(
        'undeclared_section_representation:873617f9-7681-5bd0-9fce-2706d410d648',
      ),
    );
    expect(
      readiness.issues,
      contains(
        'unregistered_pane_package:4df05965-63a7-5a27-a54f-cf479cac2545',
      ),
    );
  });

  test(
    'host bootstrap pane contributions do not require a compiled package',
    () {
      final readiness = resolveInterfacePackageRuntimeReadiness(
        registry: InterfacePackageRuntimeRegistry(),
        hostState: InterfaceHostState(
          hostLabel: 'interface-flutter-test',
          namespace: 'flutter-test',
          started: true,
          transport: _testTransportState(),
          runtime: InterfaceRuntimeState(
            backend: _testBackendState(),
            resolvedView: InterfaceResolvedView(
              experienceKey: 'aware.interface.bootstrap',
              projectionViewId: 'entry.control-plane',
              hostPayload: const <String, dynamic>{},
            ),
            resolvedPanes: <InterfaceResolvedPaneDescriptor>[
              InterfaceResolvedPaneDescriptor(
                windowKey: 'bootstrap',
                layoutKey: 'bootstrap.panes',
                sectionKey: 'interface_admission',
                paneKind: 'interface_admission',
                title: 'Interface Admission',
                summary:
                    'Create, select, pair, or resume a canonical Interface.',
                stateSourceKind: 'host_pane_contribution',
                actionKeys: const <String>[
                  'interface_admission.create_interface',
                ],
              ),
            ],
          ),
        ),
      );

      expect(readiness.ready, isTrue);
      expect(readiness.interfacePackageRuntime, isNull);
      expect(readiness.title, 'Interface Bootstrap Ready');
      expect(readiness.blocksRuntimeShell, isFalse);
    },
  );

  test('interface package identity mismatch still blocks shell entry', () {
    final registry = InterfacePackageRuntimeRegistry();
    registry.register(
      InterfacePackageRuntime(
        interfacePackageId: '11111111-1111-4111-8111-111111111111',
        interfacePackageName: 'aware-control-interface',
        panePackageRegistry: PanePackageRegistry(),
        experienceKeys: const <String>['aware.control'],
      ),
    );

    final readiness = resolveInterfacePackageRuntimeReadiness(
      registry: registry,
      hostState: InterfaceHostState(
        hostLabel: 'interface-flutter-test',
        namespace: 'flutter-test',
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware.control',
            interfacePackageId: UuidValue.fromString(
              '22222222-2222-4222-8222-222222222222',
            ),
            interfacePackageName: 'aware-control-interface',
            hostPayload: const <String, dynamic>{},
          ),
        ),
      ),
    );

    expect(
      readiness.status,
      InterfacePackageRuntimeReadinessStatus.incompatible,
    );
    expect(readiness.blocksRuntimeShell, isTrue);
    expect(
      readiness.issues,
      contains(
        'interface_package_id_mismatch:host=22222222-2222-4222-8222-222222222222 runtime=11111111-1111-4111-8111-111111111111',
      ),
    );
  });

  test('missing interface package runtime still blocks shell entry', () {
    final readiness = resolveInterfacePackageRuntimeReadiness(
      registry: InterfacePackageRuntimeRegistry(),
      hostState: InterfaceHostState(
        hostLabel: 'interface-flutter-test',
        namespace: 'flutter-test',
        started: true,
        transport: _testTransportState(),
        runtime: InterfaceRuntimeState(
          backend: _testBackendState(),
          resolvedView: InterfaceResolvedView(
            experienceKey: 'aware.control',
            interfacePackageName: 'aware-control-interface',
            hostPayload: const <String, dynamic>{},
          ),
        ),
      ),
    );

    expect(
      readiness.status,
      InterfacePackageRuntimeReadinessStatus.incompatible,
    );
    expect(
      readiness.issues,
      contains('missing_interface_package_runtime:aware-control-interface'),
    );
  });
}

PaneRenderSpec _textRenderSpec(String text) {
  return PaneRenderSpec.fromJson(_textRenderSpecPayload(text));
}

Map<String, dynamic> _textRenderSpecPayload(String text) {
  return <String, dynamic>{
    'spec_id': 'identity-admission-render-spec-v0',
    'name': 'identity_admission_default',
    'spec_version': '0.1.0',
    'pane_kind': 'identity_admission',
    'view_ref': 'aware_control_identity.identity.admission.v1',
    'projection_view_key': 'identity.admission.v1',
    'root_node_key': 'message',
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'message',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'text': text,
      },
    ],
  };
}

InterfaceTransportState _testTransportState() {
  return InterfaceTransportState(
    available: true,
    registered: true,
    authenticated: true,
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
