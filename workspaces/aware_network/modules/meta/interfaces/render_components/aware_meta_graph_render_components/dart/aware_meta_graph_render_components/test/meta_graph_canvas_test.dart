import 'package:aware_meta_graph_render_components/aware_meta_graph_render_components.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('registers Meta graph canvas render component', () {
    final builder = RenderComponentRegistryBuilder();

    registerRenderComponents(builder);

    final registry = builder.build();
    expect(registry.supports(awareMetaGraphCanvasComponentRef), isTrue);
  });

  testWidgets('renders graph snapshot nodes', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData(useMaterial3: true),
        home: Scaffold(
          body: AwareMetaGraphCanvas(
            snapshot: AwareMetaGraphSnapshot.fromInput(_graphSnapshot),
          ),
        ),
      ),
    );

    expect(find.text('ObjectConfigGraph'), findsOneWidget);
    expect(find.text('ObjectInstanceGraph'), findsOneWidget);
  });

  testWidgets('renders through PaneRenderSpec and emits action port', (
    tester,
  ) async {
    final registryBuilder = RenderComponentRegistryBuilder();
    registerRenderComponents(registryBuilder);
    final invocations = <PaneRenderActionInvocation>[];
    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'meta-graph-component-spec',
      'name': 'meta_graph_component',
      'spec_version': '0.1.0',
      'pane_kind': 'meta_graph',
      'root_node_key': 'root',
      'renderer_requirements': <Map<String, dynamic>>[
        <String, dynamic>{
          'capability_kind': kPaneRenderCapabilityKindRenderComponent,
          'capability_key': awareMetaGraphCanvasComponentRef,
        },
      ],
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindComponent,
          'component_ref': awareMetaGraphCanvasComponentRef,
          'fallback_text': 'Meta graph unavailable',
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'graph_snapshot',
              'target_property': kPaneRenderStateTargetValue,
              'json_path': r'$.graph_snapshot',
              'component_input_port_key': awareMetaGraphInputGraphSnapshot,
              'transform': kPaneRenderStateTransformRaw,
            },
            <String, dynamic>{
              'binding_key': 'selected_identity',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.selected_identity',
              'component_input_port_key': awareMetaGraphInputSelectedIdentity,
              'transform': kPaneRenderStateTransformText,
            },
          ],
          'action_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'select_identity',
              'event': kPaneRenderActionEventActivate,
              'action_key': 'meta.graph.select_identity',
              'action_kind': kPaneRenderActionKindViewAction,
              'component_action_port_key': awareMetaGraphActionSelectIdentity,
            },
          ],
        },
      ],
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData(useMaterial3: true),
        home: Scaffold(
          body: PaneRenderSpecWidget(
            spec: spec,
            paneContext: PaneContext(
              paneId: 'meta_graph',
              kind: 'meta_graph',
              parameters: const <String, dynamic>{},
            ),
            materializedState: _testMaterializedPaneState(
              paneKind: 'meta_graph',
              state: const <String, dynamic>{
                'graph_snapshot': _graphSnapshot,
                'selected_identity': 'ocg',
              },
            ),
            renderComponentRegistry: registryBuilder.build(),
            onInvokeAction: (invocation) async {
              invocations.add(invocation);
            },
          ),
        ),
      ),
    );

    expect(find.text('ObjectConfigGraph'), findsOneWidget);
    expect(find.text('Meta graph unavailable'), findsNothing);

    await tester.tap(find.text('ObjectConfigGraph'));
    await tester.pump();

    expect(invocations, hasLength(1));
    expect(invocations.single.actionKey, 'meta.graph.select_identity');
  });
}

const _graphSnapshot = <String, dynamic>{
  'nodes': <Map<String, dynamic>>[
    <String, dynamic>{
      'id': 'ocg',
      'label': 'ObjectConfigGraph',
      'object_kind': 'config',
      'stable_identity': 'aware_meta.graph.config.ObjectConfigGraph',
      'position_hint': <String, dynamic>{'x': 0.3, 'y': 0.5},
    },
    <String, dynamic>{
      'id': 'oig',
      'label': 'ObjectInstanceGraph',
      'object_kind': 'instance',
      'stable_identity': 'aware_meta.graph.instance.ObjectInstanceGraph',
      'position_hint': <String, dynamic>{'x': 0.7, 'y': 0.5},
    },
  ],
  'edges': <Map<String, dynamic>>[
    <String, dynamic>{
      'id': 'ocg-oig',
      'source_node_id': 'ocg',
      'target_node_id': 'oig',
      'relationship_kind': 'instantiates',
    },
  ],
};

InterfaceMaterializedPaneState _testMaterializedPaneState({
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
