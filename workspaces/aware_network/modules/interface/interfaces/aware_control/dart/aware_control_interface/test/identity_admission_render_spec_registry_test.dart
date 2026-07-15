import 'dart:io';

import 'package:aware_control_interface/aware_control_render_specs.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('identity admission pane source is authored before generation', () {
    final source = _identityAdmissionAuthoredSource();
    expect(source, contains('render default {'));
    expect(
      source,
      contains('view aware_control_identity.identity.admission.v1;'),
    );
    expect(source, contains('root root;'));
    expect(
      source,
      contains('bind text from state.status attr status transform text'),
    );
    expect(
      source,
      contains(
        'bind value from state.display_name attr display_name transform text;',
      ),
    );
    expect(source, contains('action activate view admit_identity'));
    expect(
      source,
      contains('input profile.display_name from display_name_input;'),
    );
    expect(
      source,
      contains('input profile.public_handle from public_handle_input;'),
    );
    expect(source, contains('input profile.bio from bio_input;'));
    expect(source, contains('style input = "multiline";'));
    expect(source, contains('component aware.content.markdown_viewer;'));
    expect(
      source,
      contains(
        'bind text from state.bio attr bio transform text port markdown;',
      ),
    );
    expect(source, isNot(contains('spec_id')));
    expect(source, isNot(contains('state_model_id')));
    expect(source, isNot(contains('pane_kind')));
  });

  test(
    'aware control static runtime enriches identity admission render spec',
    () {
      final runtime = buildAwareControlRenderSpecRuntime();
      final spec = _identityAdmissionSpec(runtime);

      expect(spec.specId, '437c600d-3f64-59b9-956a-f4c06ed2f933');
      expect(spec.name, 'identity_admission_default');
      expect(spec.specVersion, '0.1.0');
      expect(spec.paneKind, 'identity_admission');
      expect(spec.viewRef, 'aware_control_identity.identity.admission.v1');
      expect(spec.projectionViewKey, 'identity.admission.v1');
      expect(spec.stateModelId, '27dc7a7d-e719-5253-b72f-7e28158454c6');
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

      expect({
        for (final requirement in spec.rendererRequirements)
          '${requirement.capabilityKind}:${requirement.capabilityKey}':
              requirement.isRequired,
      }, containsPair('node_kind:column', true));
      expect({
        for (final requirement in spec.rendererRequirements)
          '${requirement.capabilityKind}:${requirement.capabilityKey}':
              requirement.isRequired,
      }, containsPair('node_kind:component', true));
      expect({
        for (final requirement in spec.rendererRequirements)
          '${requirement.capabilityKind}:${requirement.capabilityKey}':
              requirement.isRequired,
      }, containsPair('action_binding:$kPaneRenderActionKindViewAction', true));

      final stateAttributeConfigIds = <String, String>{
        for (final binding in _allStateBindings(spec))
          binding.bindingKey: binding.stateAttributeConfigId ?? '',
      };
      expect(
        stateAttributeConfigIds,
        containsPair('status_text', '0f345d90-ed11-57e3-b894-e0e234afc051'),
      );
      expect(
        stateAttributeConfigIds,
        containsPair(
          'display_name_value',
          'ef122c87-2caa-5837-a182-ffd0d66cbd9e',
        ),
      );
      expect(
        stateAttributeConfigIds,
        containsPair(
          'public_handle_value',
          '670f8092-f173-5a71-a3a3-551e28d0b1b4',
        ),
      );
      expect(
        stateAttributeConfigIds,
        containsPair('bio_value', '4f67b643-7f3c-5f1e-8120-212c219d6401'),
      );
      expect(
        stateAttributeConfigIds,
        containsPair('bio_text', '4f67b643-7f3c-5f1e-8120-212c219d6401'),
      );
      expect(
        stateAttributeConfigIds,
        containsPair('source_receipt', '4b112a4b-14ae-57f5-9180-3cfe83360d1d'),
      );
      for (final binding in _allStateBindings(spec)) {
        expect(binding.stateModelId, spec.stateModelId);
        expect(binding.stateAttributeConfigId, isNotNull);
      }

      final submitAction = _node(spec, 'submit').actionBindings.single;
      expect(submitAction.bindingKey, 'admit_identity');
      expect(submitAction.actionKey, 'admit_identity');
      expect(submitAction.actionKind, kPaneRenderActionKindViewAction);
      expect(submitAction.operationRef, isNull);
      expect(submitAction.sdkOperationId, isNull);
      expect(submitAction.paneConfigSdkOperationId, isNull);
      expect(
        submitAction.inputBindings.map((binding) => binding.payloadPath),
        <String>[
          'profile.display_name',
          'profile.public_handle',
          'profile.bio',
        ],
      );

      final bioInput = _node(spec, 'bio_input');
      expect({
        for (final token in bioInput.styleTokens)
          token.tokenKey: token.tokenValue,
      }, containsPair('input', 'multiline'));

      final bioPreview = _node(spec, 'bio_preview');
      expect(bioPreview.nodeKind, kPaneRenderNodeKindComponent);
      expect(bioPreview.componentRef, 'aware.content.markdown_viewer');
      expect(bioPreview.fallbackNodeKind, kPaneRenderNodeKindText);
      expect(bioPreview.fallbackText, 'Bio preview unavailable');
      expect(bioPreview.stateBindings.single.componentInputPortKey, 'markdown');
      expect(
        runtime.renderComponentRegistry.supports(
          'aware.content.markdown_viewer',
        ),
        isTrue,
      );
    },
  );

  testWidgets(
    'identity admission renders declaratively without a Dart pane package',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: InterfaceHostRuntimeShell(
            hostState: _identityAdmissionHostState(),
            interfacePackageRuntime: buildAwareControlRenderSpecRuntime(),
            panePackageRegistry: PanePackageRegistry(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Identity admission'), findsOneWidget);
      expect(find.text('ready'), findsOneWidget);
      expect(find.text('Luis Miranda'), findsWidgets);
      expect(find.text('@luis'), findsWidgets);
      expect(find.text('Human validation fixture'), findsOneWidget);
      expect(find.text('test_fixture'), findsOneWidget);
      expect(find.text('Admit identity'), findsOneWidget);
      expect(
        find.textContaining('Pane package identity is missing'),
        findsNothing,
      );
      expect(
        find.textContaining('not registered in the Dart pane runtime'),
        findsNothing,
      );
    },
  );
}

String _identityAdmissionAuthoredSource() {
  final file = _repoFile(
    'workspaces/aware_network/modules/identity/interfaces/panes/'
    'identity_admission/identity_admission.aware',
  );
  return file.readAsStringSync();
}

File _repoFile(String relativePath) {
  var directory = Directory.current;
  for (var depth = 0; depth < 12; depth += 1) {
    final candidate = File('${directory.path}/$relativePath');
    if (candidate.existsSync()) {
      return candidate;
    }
    final parent = directory.parent;
    if (parent.path == directory.path) {
      break;
    }
    directory = parent;
  }
  throw StateError(
    'Could not resolve `$relativePath` from `${Directory.current.path}`.',
  );
}

PaneRenderSpec _identityAdmissionSpec(InterfacePackageRuntime runtime) {
  return runtime.renderSpecs.singleWhere(
    (spec) => spec.paneKind == 'identity_admission',
  );
}

PaneRenderNode _node(PaneRenderSpec spec, String nodeKey) {
  return spec.nodes.singleWhere((node) => node.nodeKey == nodeKey);
}

Iterable<PaneStateBinding> _allStateBindings(PaneRenderSpec spec) {
  return spec.nodes.expand((node) => node.stateBindings);
}

InterfaceHostState _identityAdmissionHostState() {
  return InterfaceHostState(
    hostLabel: 'interface-flutter',
    namespace: 'flutter-test',
    started: true,
    transport: _testTransportState(),
    runtime: InterfaceRuntimeState(
      backend: _testBackendState(),
      resolvedView: InterfaceResolvedView(
        experienceKey: 'aware_control_identity',
        projectionViewId: 'aware_control_identity.main',
        hostPayload: <String, dynamic>{
          'window_layout': <String, dynamic>{
            'window_key': 'main',
            'layout_key': 'coordination_center',
            'frame_mode': 'grid',
            'sections': <Map<String, dynamic>>[
              <String, dynamic>{
                'section_key': 'orchestration',
                'order': 0,
                'title': 'Orchestration',
              },
            ],
          },
        },
      ),
      resolvedPanes: <InterfaceResolvedPaneDescriptor>[
        InterfaceResolvedPaneDescriptor(
          windowKey: 'main',
          layoutKey: 'coordination_center',
          sectionKey: 'orchestration',
          paneKind: 'identity_admission',
          title: 'Identity',
          viewRef: 'aware_control_identity.identity.admission.v1',
          projectionViewKey: 'identity.admission.v1',
          stateSourceKind: 'section_focus_scope_lane',
          stateProjectionHash: 'identity-hash',
        ),
      ],
      materializedPaneStates: <InterfaceMaterializedPaneState>[
        InterfaceMaterializedPaneState(
          paneStateKey:
              'main:coordination_center:orchestration:identity_admission::identity-hash',
          windowKey: 'main',
          layoutKey: 'coordination_center',
          sectionKey: 'orchestration',
          paneKind: 'identity_admission',
          projectionHash: 'identity-hash',
          status: 'materialized',
          state: <String, dynamic>{
            'status': 'ready',
            'display_name': 'Luis Miranda',
            'public_handle': '@luis',
            'bio': '# Human validation fixture',
            'provenance': <String, dynamic>{'source_kind': 'test_fixture'},
          },
          provenance: const <String, dynamic>{},
        ),
      ],
    ),
  );
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
    databaseExists: true,
    opgCount: 1,
    projectionBundleAvailable: true,
    projectionPlanCount: 1,
    tableCount: 1,
  );
}
