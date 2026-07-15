import 'dart:async';

import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid_value.dart';

void main() {
  test('parses identity admission render spec fixture', () {
    final spec = PaneRenderSpec.fromJson(identityAdmissionRenderSpecFixture);

    expect(spec.paneKind, 'identity_admission');
    expect(spec.viewRef, 'aware_control_identity.identity.admission.v1');
    expect(spec.projectionViewKey, 'identity.admission.v1');
    expect(spec.childrenOf(null).single.nodeKey, 'root');
    expect(spec.childrenOf('root').map((node) => node.nodeKey), <String>[
      'title',
      'status',
      'display_name',
      'public_handle',
      'display_name_input',
      'public_handle_input',
      'submit',
      'receipt',
    ]);
    expect(
      spec.matchesPane(
        const InterfaceShellPaneMatch(
          paneKind: 'identity_admission',
          viewRef: 'aware_control_identity.identity.admission.v1',
          projectionViewKey: 'identity.admission.v1',
        ),
      ),
      isTrue,
    );
    final actionBinding = spec.nodes
        .firstWhere((node) => node.nodeKey == 'submit')
        .actionBindings
        .single;
    expect(actionBinding.actionKey, 'admit_identity');
    expect(actionBinding.actionKind, kPaneRenderActionKindViewAction);
    expect(actionBinding.operationRef, isNull);
    expect(actionBinding.sdkOperationId, isNull);
    expect(actionBinding.paneConfigSdkOperationId, isNull);
  });

  test('caches ordered child lookups by parent', () {
    final spec = PaneRenderSpec.fromJson(identityAdmissionRenderSpecFixture);

    final rootChildren = spec.childrenOf('root');
    final repeatedRootChildren = spec.childrenOf('root');

    expect(identical(rootChildren, repeatedRootChildren), isTrue);
    expect(rootChildren.map((node) => node.nodeKey), <String>[
      'title',
      'status',
      'display_name',
      'public_handle',
      'display_name_input',
      'public_handle_input',
      'submit',
      'receipt',
    ]);
    expect(spec.childrenOf(null).single.nodeKey, 'root');
    expect(identical(spec.childrenOf(null), spec.childrenOf(null)), isTrue);
  });

  test('rejects action binding without canonical action key', () {
    expect(
      () => PaneActionBinding.fromJson(<String, dynamic>{
        'binding_key': 'send_message',
        'event': kPaneRenderActionEventActivate,
        'view_action_key': 'add_conversation_message',
      }),
      throwsA(
        isA<FormatException>()
            .having((error) => error.message, 'message', contains('action_key'))
            .having(
              (error) => error.message,
              'message',
              contains('view_action_key'),
            ),
      ),
    );
  });

  testWidgets('renders state and invokes existing pane action key', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(identityAdmissionRenderSpecFixture);
    final invocations = <PaneRenderActionInvocation>[];

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'identity-admission',
              kind: 'identity_admission',
              parameters: const <String, dynamic>{
                kPaneParamWindowKey: 'main',
                kPaneParamLayoutKey: 'coordination_center',
                kPaneParamSectionKey: 'orchestration',
              },
            ),
            materializedState: identityAdmissionMaterializedState(),
            onInvokeAction: (invocation) async {
              invocations.add(invocation);
            },
          ),
        ),
      ),
    );

    expect(find.text('Identity admission'), findsOneWidget);
    expect(find.text('ready'), findsOneWidget);
    expect(find.text('Luis'), findsWidgets);
    expect(find.text('@luis'), findsWidgets);
    expect(find.text('identity state ready'), findsOneWidget);

    await tester.enterText(find.byType(TextField).at(0), 'Luis Miranda');
    await tester.enterText(find.byType(TextField).at(1), '@lm');
    await tester.tap(find.text('Admit identity'));
    await tester.pumpAndSettle();

    expect(invocations, hasLength(1));
    final invocation = invocations.single;
    expect(invocation.actionBinding.actionKey, 'admit_identity');
    expect(invocation.actionKey, 'admit_identity');
    expect(invocation.actionKind, kPaneRenderActionKindViewAction);
    expect(invocation.operationRef, isNull);
    expect(invocation.sdkOperationId, isNull);
    expect(invocation.paneConfigSdkOperationId, isNull);
    expect(invocation.actionTarget.isSdkOperation, isFalse);
    expect(invocation.payload, <String, dynamic>{
      'profile': <String, dynamic>{
        'display_name': 'Luis Miranda',
        'public_handle': '@lm',
        'bio': 'Builder of Aware',
      },
    });
  });

  testWidgets('shows render-spec action progress while invocation is pending', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(identityAdmissionRenderSpecFixture);
    final completer = Completer<void>();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'identity-admission',
              kind: 'identity_admission',
              parameters: const <String, dynamic>{},
            ),
            materializedState: identityAdmissionMaterializedState(),
            onInvokeAction: (_) async => completer.future,
          ),
        ),
      ),
    );

    await tester.tap(find.widgetWithText(ElevatedButton, 'Admit identity'));
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    final button = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
    expect(button.onPressed, isNull);

    completer.complete();
    await tester.pumpAndSettle();

    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('shows render-spec action errors inline', (tester) async {
    final spec = PaneRenderSpec.fromJson(identityAdmissionRenderSpecFixture);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'identity-admission',
              kind: 'identity_admission',
              parameters: const <String, dynamic>{},
            ),
            materializedState: identityAdmissionMaterializedState(),
            onInvokeAction: (_) async {
              throw StateError('mock action failed');
            },
          ),
        ),
      ),
    );

    await tester.tap(find.widgetWithText(ElevatedButton, 'Admit identity'));
    await tester.pumpAndSettle();

    expect(find.textContaining('mock action failed'), findsOneWidget);
  });

  testWidgets('does not infer status tone from raw state values', (
    tester,
  ) async {
    final theme = ThemeData.light();
    final spec = PaneRenderSpec.fromJson(identityAdmissionRenderSpecFixture);

    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'identity-admission',
              kind: 'identity_admission',
              parameters: const <String, dynamic>{},
            ),
            materializedState: identityAdmissionMaterializedState(
              status: 'admitted',
            ),
          ),
        ),
      ),
    );

    final statusText = tester.widget<Text>(find.text('admitted'));
    expect(statusText.style?.color, theme.colorScheme.onSecondaryContainer);
  });

  testWidgets('uses declared status tone style token', (tester) async {
    final theme = ThemeData.light();
    final spec = PaneRenderSpec.fromJson(
      identityAdmissionRenderSpecFixtureWithStatusTone('success'),
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'identity-admission',
              kind: 'identity_admission',
              parameters: const <String, dynamic>{},
            ),
            materializedState: identityAdmissionMaterializedState(
              status: 'admitted',
            ),
          ),
        ),
      ),
    );

    final statusText = tester.widget<Text>(find.text('admitted'));
    expect(statusText.style?.color, const Color(0xFF17652A));
  });

  testWidgets('uses declared metadata and receipt status tone tokens', (
    tester,
  ) async {
    final theme = ThemeData.light();

    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: PaneRenderSpec.fromJson(
              identityAdmissionRenderSpecFixtureWithStatusTone('provenance'),
            ),
            paneContext: PaneContext(
              paneId: 'identity-admission',
              kind: 'identity_admission',
              parameters: const <String, dynamic>{},
            ),
            materializedState: identityAdmissionMaterializedState(
              status: 'mocked',
            ),
          ),
        ),
      ),
    );
    final provenanceStatusText = tester.widget<Text>(find.text('mocked'));
    expect(
      provenanceStatusText.style?.color,
      theme.colorScheme.onSurfaceVariant,
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: PaneRenderSpec.fromJson(
              identityAdmissionRenderSpecFixtureWithStatusTone('receipt'),
            ),
            paneContext: PaneContext(
              paneId: 'identity-admission',
              kind: 'identity_admission',
              parameters: const <String, dynamic>{},
            ),
            materializedState: identityAdmissionMaterializedState(
              status: 'accepted',
            ),
          ),
        ),
      ),
    );
    final receiptStatusText = tester.widget<Text>(find.text('accepted'));
    expect(
      receiptStatusText.style?.color,
      theme.colorScheme.onPrimaryContainer,
    );
  });

  testWidgets(
    'uses bound status tone target property before static tone token',
    (tester) async {
      final theme = ThemeData.light();
      final spec = PaneRenderSpec.fromJson(
        identityAdmissionRenderSpecFixtureWithBoundStatusTone(
          staticTone: 'success',
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: Scaffold(
            body: PaneRenderSpecWidget(
              spec: spec,
              paneContext: PaneContext(
                paneId: 'identity-admission',
                kind: 'identity_admission',
                parameters: const <String, dynamic>{},
              ),
              materializedState: identityAdmissionMaterializedState(
                status: 'admitted',
                statusTone: 'danger',
              ),
            ),
          ),
        ),
      );

      final statusText = tester.widget<Text>(find.text('admitted'));
      expect(statusText.style?.color, theme.colorScheme.onErrorContainer);
    },
  );

  testWidgets('renders repeat nodes with item-scoped state bindings', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(networkTerritoryRenderSpecFixture);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'network-territory',
              kind: 'network_territory',
              parameters: const <String, dynamic>{},
            ),
            materializedState: networkTerritoryMaterializedState(),
          ),
        ),
      ),
    );

    expect(find.text('Network territory'), findsOneWidget);
    expect(find.text('live'), findsOneWidget);
    expect(
      find.text('1 nodes, 1 environments, 1 hosted services'),
      findsOneWidget,
    );
    expect(find.text('kernel-node'), findsOneWidget);
    expect(find.text('http://127.0.0.1:8911'), findsOneWidget);
    expect(find.text('1'), findsWidgets);
    expect(find.text('environments'), findsOneWidget);
    expect(find.text('services'), findsOneWidget);
    expect(find.text('peers'), findsOneWidget);
    expect(find.text('Home environment'), findsOneWidget);
    expect(find.text('active'), findsWidgets);
    expect(find.text('network-service'), findsOneWidget);
    expect(find.text('http://127.0.0.1:8912'), findsOneWidget);
  });

  testWidgets('resolves nested repeat action payloads from item scope', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(networkTerritoryRenderSpecFixture);
    final invocations = <PaneRenderActionInvocation>[];

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'network-territory',
              kind: 'network_territory',
              parameters: const <String, dynamic>{},
            ),
            materializedState: networkTerritoryMaterializedState(),
            onInvokeAction: (invocation) async {
              invocations.add(invocation);
            },
          ),
        ),
      ),
    );

    await tester.tap(
      find.widgetWithText(ElevatedButton, 'Inspect environment'),
    );
    await tester.pumpAndSettle();

    expect(invocations, hasLength(1));
    final invocation = invocations.single;
    expect(invocation.actionKind, kPaneRenderActionKindApiEndpoint);
    expect(invocation.endpointRef, 'network.environment.inspect');
    expect(invocation.payload, <String, dynamic>{
      'selection': <String, dynamic>{
        'node_id': 'node-1',
        'environment_id': 'env-1',
        'node_index': 0,
        'environment_index': 0,
      },
    });
  });

  test('applies empty transforms structurally', () {
    const notEmpty = PaneStateBinding(
      bindingKey: 'visible',
      targetProperty: kPaneRenderStateTargetVisible,
      jsonPath: r'$.items',
      transform: kPaneRenderStateTransformNotEmpty,
    );
    const isEmpty = PaneStateBinding(
      bindingKey: 'empty',
      targetProperty: kPaneRenderStateTargetVisible,
      jsonPath: r'$.items',
      transform: kPaneRenderStateTransformIsEmpty,
    );

    expect(paneRenderApplyStateTransform(notEmpty, <Object>[]), isFalse);
    expect(
      paneRenderApplyStateTransform(notEmpty, <String, Object>{}),
      isFalse,
    );
    expect(paneRenderApplyStateTransform(notEmpty, <Object>[1]), isTrue);
    expect(
      paneRenderApplyStateTransform(notEmpty, <String, Object>{'a': 1}),
      isTrue,
    );
    expect(paneRenderApplyStateTransform(notEmpty, '  '), isFalse);
    expect(paneRenderApplyStateTransform(notEmpty, 'mock'), isTrue);

    expect(paneRenderApplyStateTransform(isEmpty, null), isTrue);
    expect(paneRenderApplyStateTransform(isEmpty, <Object>[]), isTrue);
    expect(paneRenderApplyStateTransform(isEmpty, <String, Object>{}), isTrue);
    expect(paneRenderApplyStateTransform(isEmpty, <Object>[1]), isFalse);
  });

  test('applies plural count transform with fallback labels', () {
    const binding = PaneStateBinding(
      bindingKey: 'issue_count',
      targetProperty: kPaneRenderStateTargetText,
      jsonPath: r'$.issues',
      transform: kPaneRenderStateTransformPluralCount,
      fallbackValue: '0 issues',
    );

    expect(paneRenderApplyStateTransform(binding, <Object>[]), '0 issues');
    expect(paneRenderApplyStateTransform(binding, <Object>[1]), '1 issue');
    expect(paneRenderApplyStateTransform(binding, <Object>[1, 2]), '2 issues');
  });

  testWidgets('renders disclosure nodes from authored goal pane shape', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'goal-disclosure-render-spec-v0',
      'name': 'goal_default',
      'spec_version': '0.1.0',
      'pane_kind': 'goal',
      'root_node_key': 'root',
      'renderer_requirements': <Map<String, dynamic>>[
        <String, dynamic>{
          'capability_kind': 'node_kind',
          'capability_key': kPaneRenderNodeKindDisclosure,
          'is_required': true,
        },
      ],
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindColumn,
        },
        <String, dynamic>{
          'node_key': 'lanes',
          'parent_node_key': 'root',
          'node_kind': kPaneRenderNodeKindRepeat,
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'lanes',
              'target_property': kPaneRenderStateTargetItems,
              'json_path': r'$.lanes',
            },
          ],
        },
        <String, dynamic>{
          'node_key': 'lanes.lane',
          'parent_node_key': 'lanes',
          'node_kind': kPaneRenderNodeKindDisclosure,
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'lane_key',
              'target_property': 'identity',
              'json_path': r'$.item.lane_key',
              'transform': kPaneRenderStateTransformText,
            },
          ],
        },
        <String, dynamic>{
          'node_key': 'lanes.lane.summary',
          'parent_node_key': 'lanes.lane',
          'node_kind': kPaneRenderNodeKindRow,
          'slot_key': 'summary',
        },
        <String, dynamic>{
          'node_key': 'lanes.lane.summary.title',
          'parent_node_key': 'lanes.lane.summary',
          'node_kind': kPaneRenderNodeKindText,
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'lane_key',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.item.lane_key',
              'transform': kPaneRenderStateTransformText,
            },
          ],
        },
        <String, dynamic>{
          'node_key': 'lanes.lane.summary.issue_count',
          'parent_node_key': 'lanes.lane.summary',
          'node_kind': kPaneRenderNodeKindText,
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'issue_count',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.item.issues',
              'transform': kPaneRenderStateTransformPluralCount,
              'fallback_value': '0 issues',
            },
          ],
        },
        <String, dynamic>{
          'node_key': 'lanes.lane.detail',
          'parent_node_key': 'lanes.lane',
          'node_kind': kPaneRenderNodeKindColumn,
          'slot_key': 'detail',
        },
        <String, dynamic>{
          'node_key': 'lanes.lane.detail.scope',
          'parent_node_key': 'lanes.lane.detail',
          'node_kind': kPaneRenderNodeKindField,
          'label': 'Scope',
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'scope',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.item.scope',
              'transform': kPaneRenderStateTransformText,
            },
          ],
        },
      ],
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'goal',
              kind: 'goal',
              parameters: const <String, dynamic>{},
            ),
            materializedState: testMaterializedPaneState(
              paneKind: 'goal',
              state: <String, dynamic>{
                'lanes': <Map<String, dynamic>>[
                  <String, dynamic>{
                    'lane_key': 'interface',
                    'scope': 'Render canonical goal pane.',
                    'issues': <Map<String, dynamic>>[
                      <String, dynamic>{'issue_ref': 'one'},
                    ],
                  },
                ],
              },
            ),
          ),
        ),
      ),
    );

    expect(find.text('interface'), findsOneWidget);
    expect(find.text('1 issue'), findsOneWidget);
    expect(find.text('Render canonical goal pane.'), findsOneWidget);
  });

  test('parses render component node refs and explicit ports', () {
    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'component-spec',
      'name': 'component_spec',
      'spec_version': '0.1.0',
      'pane_kind': 'content',
      'root_node_key': 'root',
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindColumn,
        },
        <String, dynamic>{
          'node_key': 'editor',
          'parent_node_key': 'root',
          'node_kind': kPaneRenderNodeKindComponent,
          'component_ref': 'aware.content.markdown_editor',
          'component_contract_id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          'fallback_node_kind': kPaneRenderNodeKindText,
          'fallback_text': 'Markdown preview unavailable',
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'document_markdown',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.markdown',
              'component_input_port_key': 'document',
            },
          ],
          'action_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'save_document',
              'event': kPaneRenderActionEventActivate,
              'action_key': 'api:content.document.save',
              'component_action_port_key': 'save',
            },
          ],
        },
      ],
    });

    final component = spec.nodes.singleWhere(
      (node) => node.nodeKey == 'editor',
    );
    expect(component.nodeKind, kPaneRenderNodeKindComponent);
    expect(component.componentRef, 'aware.content.markdown_editor');
    expect(
      component.componentContractId,
      'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    );
    expect(component.fallbackNodeKind, kPaneRenderNodeKindText);
    expect(component.fallbackText, 'Markdown preview unavailable');
    expect(component.stateBindings.single.componentInputPortKey, 'document');
    expect(component.actionBindings.single.componentActionPortKey, 'save');
  });

  testWidgets('renders component fallback when no native registry is present', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'component-fallback-spec',
      'name': 'component_fallback',
      'spec_version': '0.1.0',
      'pane_kind': 'content',
      'root_node_key': 'root',
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindColumn,
        },
        <String, dynamic>{
          'node_key': 'editor',
          'parent_node_key': 'root',
          'node_kind': kPaneRenderNodeKindComponent,
          'component_ref': 'aware.content.markdown_editor',
          'fallback_text': 'Markdown preview unavailable',
        },
      ],
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'content',
              kind: 'content',
              parameters: const <String, dynamic>{},
            ),
          ),
        ),
      ),
    );

    expect(find.text('Markdown preview unavailable'), findsOneWidget);
    expect(find.text('aware.content.markdown_editor'), findsOneWidget);
  });

  testWidgets(
    'renders registered component with explicit inputs and action ports',
    (tester) async {
      final spec = PaneRenderSpec.fromJson(<String, dynamic>{
        'spec_id': 'registered-component-spec',
        'name': 'registered_component',
        'spec_version': '0.1.0',
        'pane_kind': 'content',
        'root_node_key': 'root',
        'renderer_requirements': <Map<String, dynamic>>[
          <String, dynamic>{
            'capability_kind': kPaneRenderCapabilityKindRenderComponent,
            'capability_key': 'aware.content.markdown_editor',
          },
        ],
        'nodes': <Map<String, dynamic>>[
          <String, dynamic>{
            'node_key': 'root',
            'node_kind': kPaneRenderNodeKindColumn,
          },
          <String, dynamic>{
            'node_key': 'editor',
            'parent_node_key': 'root',
            'node_kind': kPaneRenderNodeKindComponent,
            'component_ref': 'aware.content.markdown_editor',
            'fallback_text': 'Markdown preview unavailable',
            'state_bindings': <Map<String, dynamic>>[
              <String, dynamic>{
                'binding_key': 'document_markdown',
                'target_property': kPaneRenderStateTargetText,
                'json_path': r'$.markdown',
                'component_input_port_key': 'document',
                'transform': kPaneRenderStateTransformText,
              },
            ],
            'action_bindings': <Map<String, dynamic>>[
              <String, dynamic>{
                'binding_key': 'save_document',
                'event': kPaneRenderActionEventActivate,
                'action_key': 'api:content.document.save',
                'action_kind': kPaneRenderActionKindApiEndpoint,
                'component_action_port_key': 'save',
              },
            ],
          },
        ],
      });
      final invocations = <PaneRenderActionInvocation>[];

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PaneRenderSpecWidget(
              spec: spec,
              paneContext: PaneContext(
                paneId: 'content',
                kind: 'content',
                parameters: const <String, dynamic>{},
              ),
              materializedState: testMaterializedPaneState(
                paneKind: 'content',
                state: const <String, dynamic>{'markdown': '# Hello'},
              ),
              renderComponentRegistry: RenderComponentRegistry
                  .fromRegistrations(<RenderComponentRegistration>[
                RenderComponentRegistration(
                  componentRef: 'aware.content.markdown_editor',
                  builder: (context, component) {
                    return ElevatedButton(
                      onPressed: () => component.invokeActionPort('save'),
                      child: Text('Native ${component.input('document')}'),
                    );
                  },
                ),
              ]),
              onInvokeAction: (invocation) async {
                invocations.add(invocation);
              },
            ),
          ),
        ),
      );

      expect(find.text('Native # Hello'), findsOneWidget);
      expect(find.text('Markdown preview unavailable'), findsNothing);
      expect(
        find.text('Pane renderer missing required capability'),
        findsNothing,
      );

      await tester.tap(find.widgetWithText(ElevatedButton, 'Native # Hello'));
      await tester.pumpAndSettle();

      expect(invocations, hasLength(1));
      expect(invocations.single.actionKey, 'api:content.document.save');
    },
  );

  testWidgets('blocks missing required renderer capabilities', (tester) async {
    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'missing-capability-spec',
      'name': 'missing_capability',
      'spec_version': '0.1.0',
      'pane_kind': 'test',
      'root_node_key': 'root',
      'renderer_requirements': <Map<String, dynamic>>[
        <String, dynamic>{
          'capability_kind': 'node_kind',
          'capability_key': 'graph_canvas',
        },
      ],
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindColumn,
        },
      ],
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'test',
              kind: 'test',
              parameters: const <String, dynamic>{},
            ),
          ),
        ),
      ),
    );

    expect(
      find.text('Pane renderer missing required capability'),
      findsOneWidget,
    );
    expect(find.text('node_kind:graph_canvas'), findsOneWidget);
  });

  testWidgets('blocks required render component capability until registered', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'missing-render-component-spec',
      'name': 'missing_render_component',
      'spec_version': '0.1.0',
      'pane_kind': 'content',
      'root_node_key': 'root',
      'renderer_requirements': <Map<String, dynamic>>[
        <String, dynamic>{
          'capability_kind': kPaneRenderCapabilityKindRenderComponent,
          'capability_key': 'aware.content.markdown_editor',
        },
      ],
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindComponent,
          'component_ref': 'aware.content.markdown_editor',
          'fallback_text': 'Markdown preview unavailable',
        },
      ],
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'content',
              kind: 'content',
              parameters: const <String, dynamic>{},
            ),
          ),
        ),
      ),
    );

    expect(
      find.text('Pane renderer missing required capability'),
      findsOneWidget,
    );
    expect(
      find.text('render_component:aware.content.markdown_editor'),
      findsOneWidget,
    );
  });

  testWidgets('blocks unknown node kinds and reserved transforms', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'unknown-node-spec',
      'name': 'unknown_node',
      'spec_version': '0.1.0',
      'pane_kind': 'test',
      'root_node_key': 'root',
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': 'sparkline',
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'reserved_equals',
              'target_property': kPaneRenderStateTargetVisible,
              'json_path': r'$.status',
              'transform': 'equals',
            },
          ],
        },
      ],
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'test',
              kind: 'test',
              parameters: const <String, dynamic>{},
            ),
            materializedState: testMaterializedPaneState(
              paneKind: 'test',
              state: const <String, dynamic>{'status': 'ready'},
            ),
          ),
        ),
      ),
    );

    expect(
      find.text('Pane renderer missing required capability'),
      findsOneWidget,
    );
    expect(
      find.text('node_kind:sparkline, state_transform:equals'),
      findsOneWidget,
    );
  });

  testWidgets('renders operational display primitives', (tester) async {
    final spec = PaneRenderSpec.fromJson(operationalDisplayRenderSpecFixture);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'operations',
              kind: 'operations',
              parameters: const <String, dynamic>{},
            ),
            materializedState: testMaterializedPaneState(
              paneKind: 'operations',
              state: const <String, dynamic>{
                'nodes': <String>['a', 'b'],
                'source': 'mock://network_territory',
              },
            ),
          ),
        ),
      ),
    );

    expect(find.text('Territory'), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(find.text('nodes'), findsOneWidget);
    expect(find.text('Source'), findsOneWidget);
    expect(find.text('mock://network_territory'), findsOneWidget);
    expect(find.text('Network node'), findsOneWidget);
    expect(find.text('ready'), findsOneWidget);
  });

  testWidgets('renders pane header and metadata bar facts declaratively', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(metadataBarRenderSpecFixture);
    final theme = ThemeData.light();

    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'goal',
              kind: 'goal',
              parameters: const <String, dynamic>{},
            ),
            materializedState: testMaterializedPaneState(
              paneKind: 'goal',
              state: const <String, dynamic>{
                'status': 'Active',
                'priority': 'P0',
                'lanes': <String>['a', 'b', 'c', 'd', 'e', 'f', 'g'],
              },
            ),
          ),
        ),
      ),
    );

    expect(find.text('Experience Attention OS'), findsOneWidget);
    expect(find.text('Active'), findsOneWidget);
    expect(find.text('P0'), findsOneWidget);
    expect(find.text('7'), findsOneWidget);
    expect(find.text('lanes'), findsOneWidget);
    final title = tester.widget<Text>(find.text('Experience Attention OS'));
    expect(title.textAlign, TextAlign.center);
    expect(title.style?.fontWeight, FontWeight.w800);
    expect(title.style?.fontSize, greaterThanOrEqualTo(20));
    final columns = tester.widgetList<Column>(find.byType(Column));
    expect(
      columns.any(
        (column) => column.crossAxisAlignment == CrossAxisAlignment.center,
      ),
      isTrue,
    );
    expect(find.byType(Wrap), findsOneWidget);
    final wrap = tester.widget<Wrap>(find.byType(Wrap));
    expect(wrap.alignment, WrapAlignment.center);
    expect(wrap.crossAxisAlignment, WrapCrossAlignment.center);
    expect(
      find.ancestor(of: find.text('7'), matching: find.byType(Row)),
      findsOneWidget,
    );
    expect(
      find.ancestor(of: find.text('lanes'), matching: find.byType(Row)),
      findsOneWidget,
    );
    expect(
      find.ancestor(of: find.text('Active'), matching: find.byType(Align)),
      findsNothing,
    );
  });

  testWidgets('uses declared provenance tone without URI heuristics', (
    tester,
  ) async {
    final theme = ThemeData.dark();
    final spec = PaneRenderSpec.fromJson(provenanceToneRenderSpecFixture);

    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'provenance',
              kind: 'provenance',
              parameters: const <String, dynamic>{},
            ),
          ),
        ),
      ),
    );

    final rawUriText = tester.widget<Text>(find.text('mock://raw-source'));
    final declaredProvenanceText = tester.widget<Text>(
      find.text('mock://declared-source'),
    );
    expect(rawUriText.style?.color, isNot(theme.colorScheme.onSurfaceVariant));
    expect(
      declaredProvenanceText.style?.color,
      theme.colorScheme.onSurfaceVariant,
    );
  });
}

Map<String, dynamic> get metadataBarRenderSpecFixture {
  return <String, dynamic>{
    'spec_id': 'metadata-bar-render-spec-v0',
    'name': 'metadata_bar_default',
    'spec_version': '0.1.0',
    'pane_kind': 'goal',
    'root_node_key': 'root',
    'renderer_requirements': <Map<String, dynamic>>[
      <String, dynamic>{
        'capability_kind': 'layout_kind',
        'capability_key': 'metadata_bar',
      },
      <String, dynamic>{
        'capability_kind': 'layout_kind',
        'capability_key': 'pane_header',
      },
    ],
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
      },
      <String, dynamic>{
        'node_key': 'header',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
        'semantic_role': 'heading',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{
            'token_key': 'layout',
            'token_value': 'pane_header',
          },
          <String, dynamic>{'token_key': 'align', 'token_value': 'center'},
        ],
      },
      <String, dynamic>{
        'node_key': 'title',
        'parent_node_key': 'header',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'heading',
        'text': 'Experience Attention OS',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{
            'token_key': 'typography',
            'token_value': 'pane_title',
          },
          <String, dynamic>{'token_key': 'align', 'token_value': 'center'},
        ],
      },
      <String, dynamic>{
        'node_key': 'metadata',
        'parent_node_key': 'header',
        'node_kind': kPaneRenderNodeKindRow,
        'semantic_role': 'status',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{
            'token_key': 'layout',
            'token_value': 'metadata_bar',
          },
          <String, dynamic>{'token_key': 'align', 'token_value': 'center'},
        ],
      },
      <String, dynamic>{
        'node_key': 'status',
        'parent_node_key': 'metadata',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'status',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.status',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'priority',
        'parent_node_key': 'metadata',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'priority',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.priority',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'lane_count',
        'parent_node_key': 'metadata',
        'node_kind': kPaneRenderNodeKindMetric,
        'semantic_role': 'metric',
        'label': 'lanes',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'lane_count',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.lanes',
            'transform': kPaneRenderStateTransformCount,
          },
        ],
      },
    ],
  };
}

Map<String, dynamic> get identityAdmissionRenderSpecFixture {
  return <String, dynamic>{
    'spec_id': 'identity-admission-render-spec-v0',
    'name': 'identity_admission_default',
    'spec_version': '0.1.0',
    'pane_kind': 'identity_admission',
    'view_ref': 'aware_control_identity.identity.admission.v1',
    'projection_view_key': 'identity.admission.v1',
    'state_model_id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'root_node_key': 'root',
    'renderer_requirements': <Map<String, dynamic>>[
      <String, dynamic>{
        'capability_kind': 'node_kind',
        'capability_key': 'column',
      },
      <String, dynamic>{
        'capability_kind': 'action_binding',
        'capability_key': 'sdk_operation',
      },
    ],
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
        'semantic_role': 'pane',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{'token_key': 'density', 'token_value': 'compact'},
        ],
      },
      <String, dynamic>{
        'node_key': 'title',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'heading',
        'order': 0,
        'text': 'Identity admission',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{'token_key': 'emphasis', 'token_value': 'primary'},
        ],
      },
      <String, dynamic>{
        'node_key': 'status',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 1,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'status_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.status',
            'state_model_id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
            'state_attribute_config_id': 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
            'transform': kPaneRenderStateTransformText,
            'fallback_value': 'ready',
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'display_name',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 2,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'display_name_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.display_name',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'public_handle',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 3,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'public_handle_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.public_handle',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'display_name_input',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindTextInput,
        'semantic_role': 'input',
        'order': 4,
        'label': 'Display name',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'display_name_value',
            'target_property': kPaneRenderStateTargetValue,
            'json_path': r'$.display_name',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'public_handle_input',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindTextInput,
        'semantic_role': 'input',
        'order': 5,
        'label': 'Public handle',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'public_handle_value',
            'target_property': kPaneRenderStateTargetValue,
            'json_path': r'$.public_handle',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'submit',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindButton,
        'semantic_role': 'action',
        'order': 6,
        'label': 'Admit identity',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{'token_key': 'emphasis', 'token_value': 'primary'},
        ],
        'action_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'admit_identity',
            'event': kPaneRenderActionEventActivate,
            'action_key': 'admit_identity',
            'action_kind': kPaneRenderActionKindViewAction,
            'label': 'Admit identity',
            'receipt_policy': 'show_receipt',
            'input_bindings': <Map<String, dynamic>>[
              <String, dynamic>{
                'payload_path': 'profile.display_name',
                'source_node_key': 'display_name_input',
              },
              <String, dynamic>{
                'payload_path': 'profile.public_handle',
                'source_node_key': 'public_handle_input',
              },
              <String, dynamic>{
                'payload_path': 'profile.bio',
                'source_json_path': r'$.bio',
              },
            ],
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'receipt',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindReceipt,
        'semantic_role': 'receipt',
        'order': 7,
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{'token_key': 'tone', 'token_value': 'receipt'},
        ],
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'source_receipt',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.receipt.summary',
            'transform': kPaneRenderStateTransformText,
          },
          <String, dynamic>{
            'binding_key': 'source_receipt_visible',
            'target_property': kPaneRenderStateTargetVisible,
            'json_path': r'$.receipt.summary',
            'transform': kPaneRenderStateTransformNotEmpty,
          },
        ],
      },
    ],
  };
}

Map<String, dynamic> identityAdmissionRenderSpecFixtureWithStatusTone(
  String tone,
) {
  final base = identityAdmissionRenderSpecFixture;
  final nodes = (base['nodes'] as List<Map<String, dynamic>>)
      .map((node) => Map<String, dynamic>.from(node))
      .toList(growable: false);
  final status = nodes.firstWhere((node) => node['node_key'] == 'status');
  status['style_tokens'] = <Map<String, dynamic>>[
    <String, dynamic>{'token_key': 'tone', 'token_value': tone},
  ];
  return <String, dynamic>{...base, 'nodes': nodes};
}

Map<String, dynamic> identityAdmissionRenderSpecFixtureWithBoundStatusTone({
  String? staticTone,
}) {
  final base = staticTone == null
      ? identityAdmissionRenderSpecFixture
      : identityAdmissionRenderSpecFixtureWithStatusTone(staticTone);
  final nodes = (base['nodes'] as List<Map<String, dynamic>>)
      .map((node) => Map<String, dynamic>.from(node))
      .toList(growable: false);
  final status = nodes.firstWhere((node) => node['node_key'] == 'status');
  final stateBindings = (status['state_bindings'] as List<Map<String, dynamic>>)
      .map((binding) => Map<String, dynamic>.from(binding))
      .toList(growable: true);
  stateBindings.add(<String, dynamic>{
    'binding_key': 'status_tone',
    'target_property': kPaneRenderStateTargetTone,
    'json_path': r'$.status_tone',
    'state_model_id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'state_attribute_config_id': 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    'transform': kPaneRenderStateTransformText,
  });
  status['state_bindings'] = stateBindings;
  return <String, dynamic>{...base, 'nodes': nodes};
}

InterfaceMaterializedPaneState identityAdmissionMaterializedState({
  String status = 'ready',
  String? statusTone,
}) {
  return InterfaceMaterializedPaneState(
    paneStateKey:
        'main:coordination_center:orchestration:identity_admission:cccccccc-cccc-4ccc-8ccc-cccccccccccc:identity-hash',
    windowKey: 'main',
    layoutKey: 'coordination_center',
    sectionKey: 'orchestration',
    paneKind: 'identity_admission',
    paneConfigId: UuidValue.fromString('cccccccc-cccc-4ccc-8ccc-cccccccccccc'),
    projectionExperienceViewId: UuidValue.fromString(
      'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    ),
    projectionViewId: 'identity.admission.v1',
    stateModelId: UuidValue.fromString('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'),
    projectionHash: 'identity-hash',
    status: 'materialized',
    state: <String, dynamic>{
      'status': status,
      if (statusTone != null) 'status_tone': statusTone,
      'display_name': 'Luis',
      'public_handle': '@luis',
      'bio': 'Builder of Aware',
      'provenance': <String, dynamic>{
        'source_kind': 'interface_host_fanout_materialization',
      },
      'receipt': <String, dynamic>{
        'summary': 'identity state ready',
        'action_count': 0,
      },
    },
    provenance: const <String, dynamic>{
      'source_kind': 'interface_host_fanout_materialization',
    },
  );
}

InterfaceMaterializedPaneState testMaterializedPaneState({
  required String paneKind,
  required Map<String, dynamic> state,
}) {
  return InterfaceMaterializedPaneState(
    paneStateKey: 'test:window:layout:section:$paneKind:test-hash',
    windowKey: 'test',
    layoutKey: 'layout',
    sectionKey: 'section',
    paneKind: paneKind,
    projectionViewId: 'test.view',
    projectionHash: 'test-hash',
    status: 'materialized',
    state: state,
    provenance: const <String, dynamic>{},
  );
}

Map<String, dynamic> get networkTerritoryRenderSpecFixture {
  return <String, dynamic>{
    'spec_id': 'network-territory-render-spec-v0',
    'name': 'network_territory_default',
    'spec_version': '0.1.0',
    'pane_kind': 'network_territory',
    'view_ref': 'aware_network.territory.discovery.v1',
    'projection_view_key': 'territory.discovery.v1',
    'state_model_id': '99999999-9999-4999-8999-999999999999',
    'root_node_key': 'root',
    'renderer_requirements': <Map<String, dynamic>>[
      <String, dynamic>{
        'capability_kind': 'node_kind',
        'capability_key': 'repeat',
      },
    ],
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindScroll,
        'semantic_role': 'pane',
      },
      <String, dynamic>{
        'node_key': 'title',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'heading',
        'order': 0,
        'text': 'Network territory',
      },
      <String, dynamic>{
        'node_key': 'status',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 1,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'status_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.status',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'summary',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 2,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'summary_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.summary',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'nodes',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindRepeat,
        'semantic_role': 'section',
        'order': 3,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'nodes_items',
            'target_property': kPaneRenderStateTargetItems,
            'json_path': r'$.nodes',
            'transform': kPaneRenderStateTransformRaw,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'node_card',
        'parent_node_key': 'nodes',
        'node_kind': kPaneRenderNodeKindBox,
        'semantic_role': 'section',
        'order': 0,
      },
      <String, dynamic>{
        'node_key': 'node_title',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'heading',
        'order': 0,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'node_title',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.node.hostname',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'node_route',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 1,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'node_route',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.node.base_url',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'counts',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindRow,
        'semantic_role': 'section',
        'order': 2,
      },
      <String, dynamic>{
        'node_key': 'environment_count',
        'parent_node_key': 'counts',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 0,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'environment_count',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.environments',
            'transform': kPaneRenderStateTransformCount,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'environment_label',
        'parent_node_key': 'counts',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 1,
        'text': 'environments',
      },
      <String, dynamic>{
        'node_key': 'service_count',
        'parent_node_key': 'counts',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 2,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'service_count',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.hosted_services',
            'transform': kPaneRenderStateTransformCount,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'service_label',
        'parent_node_key': 'counts',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 3,
        'text': 'services',
      },
      <String, dynamic>{
        'node_key': 'peer_count',
        'parent_node_key': 'counts',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 4,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'peer_count',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.peers',
            'transform': kPaneRenderStateTransformCount,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'peer_label',
        'parent_node_key': 'counts',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 5,
        'text': 'peers',
      },
      <String, dynamic>{
        'node_key': 'environment_section_label',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 3,
        'text': 'Environment details',
      },
      <String, dynamic>{
        'node_key': 'environments',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindRepeat,
        'semantic_role': 'section',
        'order': 4,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'environments_items',
            'target_property': kPaneRenderStateTargetItems,
            'json_path': r'$.item.environments',
            'transform': kPaneRenderStateTransformRaw,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'environment_row',
        'parent_node_key': 'environments',
        'node_kind': kPaneRenderNodeKindRow,
        'semantic_role': 'section',
        'order': 0,
      },
      <String, dynamic>{
        'node_key': 'environment_title',
        'parent_node_key': 'environment_row',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 0,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'environment_title',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.environment_title',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'environment_status',
        'parent_node_key': 'environment_row',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 1,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'environment_status',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.status',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'inspect_environment',
        'parent_node_key': 'environment_row',
        'node_kind': kPaneRenderNodeKindButton,
        'semantic_role': 'action',
        'order': 2,
        'label': 'Inspect environment',
        'action_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'inspect_environment',
            'event': kPaneRenderActionEventActivate,
            'action_key': 'api:network.environment.inspect',
            'action_kind': 'api_endpoint',
            'api_endpoint_ref': 'network.environment.inspect',
            'label': 'Inspect environment',
            'input_bindings': <Map<String, dynamic>>[
              <String, dynamic>{
                'payload_path': 'selection.node_id',
                'source_json_path': r'$.parent.node.node_id',
              },
              <String, dynamic>{
                'payload_path': 'selection.environment_id',
                'source_json_path': r'$.item.environment_id',
              },
              <String, dynamic>{
                'payload_path': 'selection.node_index',
                'source_json_path': r'$.parent_index',
              },
              <String, dynamic>{
                'payload_path': 'selection.environment_index',
                'source_json_path': r'$.item_index',
              },
            ],
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'service_section_label',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 5,
        'text': 'Hosted services',
      },
      <String, dynamic>{
        'node_key': 'hosted_services',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindRepeat,
        'semantic_role': 'section',
        'order': 6,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'hosted_services_items',
            'target_property': kPaneRenderStateTargetItems,
            'json_path': r'$.item.hosted_services',
            'transform': kPaneRenderStateTransformRaw,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'service_row',
        'parent_node_key': 'hosted_services',
        'node_kind': kPaneRenderNodeKindRow,
        'semantic_role': 'section',
        'order': 0,
      },
      <String, dynamic>{
        'node_key': 'service_name',
        'parent_node_key': 'service_row',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 0,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'service_name',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.service_name',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'service_endpoint_count',
        'parent_node_key': 'service_row',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 1,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'service_endpoint_count',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.endpoint_refs',
            'transform': kPaneRenderStateTransformCount,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'peer_section_label',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 7,
        'text': 'Peers',
      },
      <String, dynamic>{
        'node_key': 'peers',
        'parent_node_key': 'node_card',
        'node_kind': kPaneRenderNodeKindRepeat,
        'semantic_role': 'section',
        'order': 8,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'peers_items',
            'target_property': kPaneRenderStateTargetItems,
            'json_path': r'$.item.peers',
            'transform': kPaneRenderStateTransformRaw,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'peer_row',
        'parent_node_key': 'peers',
        'node_kind': kPaneRenderNodeKindRow,
        'semantic_role': 'section',
        'order': 0,
      },
      <String, dynamic>{
        'node_key': 'peer_url',
        'parent_node_key': 'peer_row',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'paragraph',
        'order': 0,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'peer_url',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.peer_base_url',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'peer_status',
        'parent_node_key': 'peer_row',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 1,
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'peer_status',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.item.status',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
    ],
  };
}

Map<String, dynamic> get operationalDisplayRenderSpecFixture {
  return <String, dynamic>{
    'spec_id': 'operational-display-render-spec-v0',
    'name': 'operational_display_default',
    'spec_version': '0.1.0',
    'pane_kind': 'operations',
    'root_node_key': 'root',
    'renderer_requirements': <Map<String, dynamic>>[
      <String, dynamic>{
        'capability_kind': 'node_kind',
        'capability_key': kPaneRenderNodeKindMetric,
      },
      <String, dynamic>{
        'capability_kind': 'node_kind',
        'capability_key': kPaneRenderNodeKindField,
      },
    ],
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
      },
      <String, dynamic>{
        'node_key': 'territory_header',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindSectionHeader,
        'semantic_role': 'heading',
        'order': 0,
        'text': 'Territory',
      },
      <String, dynamic>{
        'node_key': 'node_metric',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindMetric,
        'semantic_role': 'metric',
        'order': 1,
        'label': 'nodes',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'node_count',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.nodes',
            'transform': kPaneRenderStateTransformCount,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'source_field',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindField,
        'semantic_role': 'metadata',
        'order': 2,
        'label': 'Source',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'source',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.source',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'node_item',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindListItem,
        'semantic_role': 'section',
        'order': 3,
        'text': 'Network node',
      },
      <String, dynamic>{
        'node_key': 'node_status',
        'parent_node_key': 'node_item',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'order': 0,
        'text': 'ready',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{'token_key': 'tone', 'token_value': 'success'},
        ],
      },
    ],
  };
}

Map<String, dynamic> get provenanceToneRenderSpecFixture {
  return <String, dynamic>{
    'spec_id': 'provenance-tone-render-spec-v0',
    'name': 'provenance_tone_default',
    'spec_version': '0.1.0',
    'pane_kind': 'provenance',
    'root_node_key': 'root',
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
      },
      <String, dynamic>{
        'node_key': 'raw_uri',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'metadata',
        'order': 0,
        'text': 'mock://raw-source',
      },
      <String, dynamic>{
        'node_key': 'declared_uri',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'metadata',
        'order': 1,
        'text': 'mock://declared-source',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{'token_key': 'tone', 'token_value': 'provenance'},
        ],
      },
    ],
  };
}

InterfaceMaterializedPaneState networkTerritoryMaterializedState() {
  return InterfaceMaterializedPaneState(
    paneStateKey:
        'main:coordination_center:inspector:network_territory:77777777-7777-4777-8777-777777777777:network-hash',
    windowKey: 'main',
    layoutKey: 'coordination_center',
    sectionKey: 'inspector',
    paneKind: 'network_territory',
    paneConfigId: UuidValue.fromString('77777777-7777-4777-8777-777777777777'),
    projectionExperienceViewId: UuidValue.fromString(
      '88888888-8888-4888-8888-888888888888',
    ),
    projectionViewId: 'territory.discovery.v1',
    stateModelId: UuidValue.fromString('99999999-9999-4999-8999-999999999999'),
    projectionHash: 'network-hash',
    status: 'materialized',
    state: <String, dynamic>{
      'status': 'live',
      'summary': '1 nodes, 1 environments, 1 hosted services',
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node': <String, dynamic>{
            'node_id': 'node-1',
            'hostname': 'kernel-node',
            'base_url': 'http://127.0.0.1:8911',
            'status': 'active',
          },
          'environments': <Map<String, dynamic>>[
            <String, dynamic>{
              'environment_id': 'env-1',
              'environment_title': 'Home environment',
              'status': 'active',
            },
          ],
          'hosted_services': <Map<String, dynamic>>[
            <String, dynamic>{
              'service_name': 'network-service',
              'endpoint_refs': <String>['network.discovery.discover_territory'],
            },
          ],
          'peers': <Map<String, dynamic>>[
            <String, dynamic>{'peer_base_url': 'http://127.0.0.1:8912'},
          ],
        },
      ],
      'provenance': <String, dynamic>{
        'source_kind': 'network_service_api',
        'node_count': 1,
        'environment_count': 1,
        'hosted_service_count': 1,
      },
    },
    provenance: const <String, dynamic>{
      'source_kind': 'interface_host_fanout_materialization',
    },
  );
}
