import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid_value.dart';

void main() {
  testWidgets('retains text input edits across stale host refreshes', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(_singleInputRenderSpec);

    await tester.pumpWidget(_host(spec, _state(displayName: 'Luis')));
    await tester.enterText(find.byType(TextField), 'Luis Miranda');

    await tester.pumpWidget(_host(spec, _state(displayName: 'Luis')));
    await tester.pump();

    expect(_textFieldController(tester).text, 'Luis Miranda');

    await tester.pumpWidget(_host(spec, _state(displayName: 'Luis Miranda')));
    await tester.pump();

    expect(_textFieldController(tester).text, 'Luis Miranda');

    await tester.pumpWidget(_host(spec, _state(displayName: 'Luis Lechuga')));
    await tester.pump();

    expect(_textFieldController(tester).text, 'Luis Lechuga');
  });

  testWidgets('renders local input drafts through component state bindings', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(_inputAndComponentRenderSpec);
    final previews = <Object?>[];
    final registry =
        RenderComponentRegistry.fromRegistrations(<RenderComponentRegistration>[
      RenderComponentRegistration(
        componentRef: 'aware.content.markdown_viewer',
        builder: (context, component) {
          final markdown = component.input('markdown');
          previews.add(markdown);
          return Text('Preview ${markdown ?? ''}');
        },
      ),
    ]);

    await tester.pumpWidget(
      _host(
        spec,
        _state(displayName: 'Luis', bio: ''),
        registry: registry,
      ),
    );

    expect(find.text('Preview '), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'Hello World');
    await tester.pump();

    expect(_textFieldController(tester).text, 'Hello World');
    expect(previews.length, greaterThan(1));
    expect(previews.last, 'Hello World');
    expect(find.text('Preview Hello World'), findsOneWidget);

    await tester.pumpWidget(
      _host(
        spec,
        _state(displayName: 'Luis', bio: ''),
        registry: registry,
      ),
    );
    await tester.pump();

    expect(find.text('Preview Hello World'), findsOneWidget);

    await tester.pumpWidget(
      _host(
        spec,
        _state(displayName: 'Luis', bio: 'Committed Bio'),
        registry: registry,
      ),
    );
    await tester.pump();

    expect(_textFieldController(tester).text, 'Committed Bio');
    expect(find.text('Preview Committed Bio'), findsOneWidget);
  });

  testWidgets('renders summary bar facts on one row', (tester) async {
    final spec = PaneRenderSpec.fromJson(_summaryBarRenderSpec);

    await tester.pumpWidget(
      _host(
        spec,
        _state(
          displayName: 'Luis',
          extraState: const <String, dynamic>{
            'lane_key': 'interface-action-rail',
            'status': 'Closed',
            'status_tone': 'success',
            'issues': <Object>[
              <String, Object>{'title': 'Issue'},
            ],
          },
        ),
      ),
    );
    await tester.pump();

    final titleCenter = tester.getCenter(find.text('interface-action-rail'));
    final statusCenter = tester.getCenter(find.text('Closed'));
    final countCenter = tester.getCenter(find.text('1 issue'));

    expect((titleCenter.dy - statusCenter.dy).abs(), lessThan(14));
    expect((titleCenter.dy - countCenter.dy).abs(), lessThan(14));
  });

  testWidgets('reports pane render-spec build tags when recorder is provided', (
    tester,
  ) async {
    final spec = PaneRenderSpec.fromJson(_singleInputRenderSpec);
    final builds = <String>[];

    await tester.pumpWidget(
      _host(
        spec,
        _state(displayName: 'Luis'),
        onBuild: builds.add,
      ),
    );
    await tester.pump();

    expect(builds, contains('PaneRenderSpecWidget:identity_admission'));
  });

  testWidgets('renders pre-resolved storage media from media_ref binding', (
    tester,
  ) async {
    final mediaRef = _storageMediaRef();
    final resolution = _storageMediaResolution(mediaRef);
    final spec = PaneRenderSpec.fromJson(_storageMediaRenderSpec);

    await tester.pumpWidget(
      _host(
        spec,
        _state(
          displayName: 'Luis',
          extraState: <String, dynamic>{
            'hero': <String, dynamic>{'image': resolution.toJson()},
          },
        ),
      ),
    );
    await tester.pump();

    final image = tester.widget<Image>(find.byType(Image));
    expect((image.image as NetworkImage).url, resolution.httpUrl);
  });

  testWidgets('resolves storage media_ref binding through Interface resolver', (
    tester,
  ) async {
    final mediaRef = _storageMediaRef();
    final resolvedRefs = <StorageMediaRef>[];
    final resolver = InterfaceStorageMediaResolver.withResolver(
      resolve: ({
        required StorageMediaRef mediaRef,
        UuidValue? actorId,
        required bool includeHttpUrl,
        String? preferredUriScheme,
        String? filename,
        required StorageMediaDisposition disposition,
        required Duration timeout,
      }) async {
        resolvedRefs.add(mediaRef);
        return _storageMediaResolution(mediaRef);
      },
    );
    final spec = PaneRenderSpec.fromJson(_storageMediaRenderSpec);

    await tester.pumpWidget(
      _host(
        spec,
        _state(
          displayName: 'Luis',
          extraState: <String, dynamic>{
            'hero': <String, dynamic>{'image': mediaRef.toJson()},
          },
        ),
        mediaResolver: resolver,
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(resolvedRefs.single.objectId, mediaRef.objectId);
    final image = tester.widget<Image>(find.byType(Image));
    expect(
      (image.image as NetworkImage).url,
      'http://storage.test/media/${mediaRef.objectId.uuid}',
    );
  });
}

Widget _host(
  PaneRenderSpec spec,
  InterfaceMaterializedPaneState materializedState, {
  RenderComponentRegistry registry = const RenderComponentRegistry.empty(),
  InterfaceStorageMediaResolver? mediaResolver,
  ValueChanged<String>? onBuild,
}) {
  return MaterialApp(
    home: Scaffold(
      body: PaneRenderSpecWidget(
        spec: spec,
        paneContext: PaneContext(
          paneId: 'identity-admission',
          kind: 'identity_admission',
          parameters: const <String, dynamic>{},
        ),
        materializedState: materializedState,
        renderComponentRegistry: registry,
        mediaResolver: mediaResolver,
        onBuild: onBuild,
      ),
    ),
  );
}

TextEditingController _textFieldController(WidgetTester tester) {
  return tester.widget<TextField>(find.byType(TextField)).controller!;
}

InterfaceMaterializedPaneState _state({
  required String displayName,
  String? bio,
  Map<String, dynamic> extraState = const <String, dynamic>{},
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
      'display_name': displayName,
      if (bio != null) 'bio': bio,
      ...extraState,
    },
    provenance: const <String, dynamic>{},
  );
}

StorageMediaRef _storageMediaRef() {
  return StorageMediaRef(
    objectId: UuidValue.fromString('77777777-7777-4777-8777-777777777777'),
    uri: 'storage://blob/77777777-7777-4777-8777-777777777777',
    uriScheme: 'storage',
    mediaKind: 'image',
    mimeType: 'image/png',
    filename: 'hero.png',
    metadata: const <String, dynamic>{},
  );
}

StorageMediaResolution _storageMediaResolution(StorageMediaRef mediaRef) {
  return StorageMediaResolution(
    mediaRef: mediaRef,
    objectId: mediaRef.objectId,
    sha: mediaRef.sha ?? 'sha256:hero',
    mimeType: mediaRef.mimeType ?? 'image/png',
    sizeBytes: 42,
    uri: mediaRef.uri ?? 'storage://blob/${mediaRef.objectId.uuid}',
    uriScheme: mediaRef.uriScheme,
    httpUrl: 'http://storage.test/media/${mediaRef.objectId.uuid}',
    filename: mediaRef.filename,
    metadata: const <String, dynamic>{},
  );
}

Map<String, dynamic> get _summaryBarRenderSpec {
  return <String, dynamic>{
    'spec_id': 'summary-bar-render-spec-v0',
    'name': 'summary_bar',
    'spec_version': '0.1.0',
    'pane_kind': 'identity_admission',
    'root_node_key': 'root',
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
        'semantic_role': 'pane',
      },
      <String, dynamic>{
        'node_key': 'lane',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindDisclosure,
        'semantic_role': 'section',
      },
      <String, dynamic>{
        'node_key': 'lane.summary',
        'parent_node_key': 'lane',
        'node_kind': kPaneRenderNodeKindRow,
        'semantic_role': 'metadata',
        'slot_key': 'summary',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{
            'token_key': 'layout',
            'token_value': 'summary_bar',
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'lane.summary.key',
        'parent_node_key': 'lane.summary',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'heading',
        'style_tokens': <Map<String, dynamic>>[
          <String, dynamic>{'token_key': 'overflow', 'token_value': 'truncate'},
        ],
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'lane_key_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.lane_key',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'lane.summary.status',
        'parent_node_key': 'lane.summary',
        'node_kind': kPaneRenderNodeKindStatus,
        'semantic_role': 'status',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'status_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.status',
            'transform': kPaneRenderStateTransformText,
          },
          <String, dynamic>{
            'binding_key': 'status_tone',
            'target_property': kPaneRenderStateTargetTone,
            'json_path': r'$.status_tone',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'lane.summary.issue_count',
        'parent_node_key': 'lane.summary',
        'node_kind': kPaneRenderNodeKindText,
        'semantic_role': 'metadata',
        'label': 'issue',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'issues_text',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.issues',
            'transform': kPaneRenderStateTransformPluralCount,
            'fallback_value': '0 issues',
          },
        ],
      },
    ],
  };
}

Map<String, dynamic> get _inputAndComponentRenderSpec {
  return <String, dynamic>{
    'spec_id': 'input-component-render-spec-v0',
    'name': 'input_component',
    'spec_version': '0.1.0',
    'pane_kind': 'identity_admission',
    'root_node_key': 'root',
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
        'semantic_role': 'pane',
      },
      <String, dynamic>{
        'node_key': 'bio_input',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindTextInput,
        'semantic_role': 'input',
        'label': 'Bio',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'bio_value',
            'target_property': kPaneRenderStateTargetValue,
            'json_path': r'$.bio',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
      <String, dynamic>{
        'node_key': 'bio_preview',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindComponent,
        'component_ref': 'aware.content.markdown_viewer',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'bio_markdown',
            'target_property': kPaneRenderStateTargetText,
            'json_path': r'$.bio',
            'component_input_port_key': 'markdown',
            'transform': kPaneRenderStateTransformText,
          },
        ],
      },
    ],
  };
}

Map<String, dynamic> get _storageMediaRenderSpec {
  return <String, dynamic>{
    'spec_id': 'storage-media-render-spec-v0',
    'name': 'storage_media',
    'spec_version': '0.1.0',
    'pane_kind': 'identity_admission',
    'root_node_key': 'root',
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
        'semantic_role': 'pane',
      },
      <String, dynamic>{
        'node_key': 'hero_image',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindComponent,
        'component_ref': 'aware.storage.media.image',
        'label': 'Hero image',
        'state_bindings': <Map<String, dynamic>>[
          <String, dynamic>{
            'binding_key': 'hero_image_media',
            'target_property': kPaneRenderStateTargetMediaRef,
            'json_path': r'$.hero.image',
            'transform': kPaneRenderStateTransformRaw,
          },
        ],
      },
    ],
  };
}

Map<String, dynamic> get _singleInputRenderSpec {
  return <String, dynamic>{
    'spec_id': 'single-input-render-spec-v0',
    'name': 'single_input',
    'spec_version': '0.1.0',
    'pane_kind': 'identity_admission',
    'root_node_key': 'root',
    'nodes': <Map<String, dynamic>>[
      <String, dynamic>{
        'node_key': 'root',
        'node_kind': kPaneRenderNodeKindColumn,
        'semantic_role': 'pane',
      },
      <String, dynamic>{
        'node_key': 'display_name_input',
        'parent_node_key': 'root',
        'node_kind': kPaneRenderNodeKindTextInput,
        'semantic_role': 'input',
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
    ],
  };
}
