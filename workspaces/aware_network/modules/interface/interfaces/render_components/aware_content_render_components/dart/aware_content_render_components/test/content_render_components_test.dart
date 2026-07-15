import 'package:aware_content_render_components/aware_content_render_components.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('registers content render components', () {
    final builder = RenderComponentRegistryBuilder();

    registerRenderComponents(builder);

    final registry = builder.build();
    expect(registry.supports(awareContentMarkdownViewerComponentRef), isTrue);
    expect(registry.supports(awareContentCodeViewerComponentRef), isTrue);
  });

  testWidgets('markdown viewer renders explicit markdown input', (
    tester,
  ) async {
    final registryBuilder = RenderComponentRegistryBuilder();
    registerRenderComponents(registryBuilder);

    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'content-markdown-component-spec',
      'name': 'content_markdown_component',
      'spec_version': '0.1.0',
      'pane_kind': 'content',
      'root_node_key': 'root',
      'renderer_requirements': <Map<String, dynamic>>[
        <String, dynamic>{
          'capability_kind': kPaneRenderCapabilityKindRenderComponent,
          'capability_key': awareContentMarkdownViewerComponentRef,
        },
      ],
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindComponent,
          'component_ref': awareContentMarkdownViewerComponentRef,
          'fallback_text': 'Markdown unavailable',
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'markdown',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.markdown',
              'component_input_port_key': 'markdown',
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
              paneId: 'content',
              kind: 'content',
              parameters: const <String, dynamic>{},
            ),
            materializedState: testMaterializedPaneState(
              paneKind: 'content',
              state: const <String, dynamic>{'markdown': '# Hello content'},
            ),
            renderComponentRegistry: registryBuilder.build(),
          ),
        ),
      ),
    );

    expect(find.text('Hello content'), findsOneWidget);
    expect(find.text('Markdown unavailable'), findsNothing);
  });

  testWidgets('markdown viewer renders structured content blocks', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
        home: const Scaffold(
          body: AwareContentMarkdownViewer(
            markdownText: '''
# Profile
Builder of **Aware** with `pane` receipts.

- Human interface
- Agent rail

> Canonical receipts stay visible.

```text
status: admitted
```
''',
          ),
        ),
      ),
    );

    expect(find.text('Profile'), findsOneWidget);
    expect(_selectablePlainText('Builder of Aware with pane receipts.'),
        findsOneWidget);
    expect(_selectablePlainText('Human interface'), findsOneWidget);
    expect(_selectablePlainText('Agent rail'), findsOneWidget);
    expect(
      _selectablePlainText('Canonical receipts stay visible.'),
      findsOneWidget,
    );
    expect(find.textContaining('status: admitted'), findsOneWidget);
  });

  testWidgets('markdown viewer renders empty state', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: AwareContentMarkdownViewer(markdownText: '')),
      ),
    );

    expect(find.text('No content yet'), findsOneWidget);
  });

  testWidgets('code viewer renders explicit code input', (tester) async {
    final registryBuilder = RenderComponentRegistryBuilder();
    registerRenderComponents(registryBuilder);

    final spec = PaneRenderSpec.fromJson(<String, dynamic>{
      'spec_id': 'content-code-component-spec',
      'name': 'content_code_component',
      'spec_version': '0.1.0',
      'pane_kind': 'content',
      'root_node_key': 'root',
      'renderer_requirements': <Map<String, dynamic>>[
        <String, dynamic>{
          'capability_kind': kPaneRenderCapabilityKindRenderComponent,
          'capability_key': awareContentCodeViewerComponentRef,
        },
      ],
      'nodes': <Map<String, dynamic>>[
        <String, dynamic>{
          'node_key': 'root',
          'node_kind': kPaneRenderNodeKindComponent,
          'component_ref': awareContentCodeViewerComponentRef,
          'fallback_text': 'Code unavailable',
          'state_bindings': <Map<String, dynamic>>[
            <String, dynamic>{
              'binding_key': 'code',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.code',
              'component_input_port_key': 'code',
              'transform': kPaneRenderStateTransformText,
            },
            <String, dynamic>{
              'binding_key': 'language',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.language',
              'component_input_port_key': 'language',
              'transform': kPaneRenderStateTransformText,
            },
            <String, dynamic>{
              'binding_key': 'title',
              'target_property': kPaneRenderStateTargetText,
              'json_path': r'$.title',
              'component_input_port_key': 'title',
              'transform': kPaneRenderStateTransformText,
            },
          ],
        },
      ],
    });

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
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
              state: const <String, dynamic>{
                'title': 'Admission receipt',
                'language': 'dart',
                'code': 'final admitted = true;',
              },
            ),
            renderComponentRegistry: registryBuilder.build(),
          ),
        ),
      ),
    );

    expect(find.text('Admission receipt'), findsOneWidget);
    expect(find.text('dart'), findsOneWidget);
    expect(find.text('final admitted = true;'), findsOneWidget);
    expect(find.text('Code unavailable'), findsNothing);
  });

  testWidgets('code viewer renders empty state', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: AwareContentCodeViewer(code: '')),
      ),
    );

    expect(find.text('No code yet'), findsOneWidget);
  });
}

Finder _selectablePlainText(String text) {
  return find.byWidgetPredicate(
    (widget) =>
        widget is SelectableText &&
        (widget.data == text || widget.textSpan?.toPlainText() == text),
    description: 'SelectableText with plain text "$text"',
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
