library aware_control_render_specs;

import 'package:aware_content_render_components/aware_content_render_components.dart'
    as aware_content_render_components;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';

List<PaneRenderSpec> buildAwareControlPaneRenderSpecs() {
  return const <PaneRenderSpec>[
    PaneRenderSpec(
      specId: '437c600d-3f64-59b9-956a-f4c06ed2f933',
      name: 'identity_admission_default',
      specVersion: '0.1.0',
      paneKind: 'identity_admission',
      viewRef: 'aware_control_identity.identity.admission.v1',
      projectionViewKey: 'identity.admission.v1',
      stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
      rootNodeKey: 'root',
      rendererRequirements: <PaneRendererCapabilityRequirement>[
        PaneRendererCapabilityRequirement(
          capabilityKind: 'node_kind',
          capabilityKey: kPaneRenderNodeKindColumn,
        ),
        PaneRendererCapabilityRequirement(
          capabilityKind: 'node_kind',
          capabilityKey: kPaneRenderNodeKindTextInput,
        ),
        PaneRendererCapabilityRequirement(
          capabilityKind: 'node_kind',
          capabilityKey: kPaneRenderNodeKindComponent,
        ),
        PaneRendererCapabilityRequirement(
          capabilityKind: 'action_binding',
          capabilityKey: kPaneRenderActionKindViewAction,
        ),
      ],
      nodes: <PaneRenderNode>[
        PaneRenderNode(
          nodeKey: 'root',
          nodeKind: kPaneRenderNodeKindColumn,
          semanticRole: 'pane',
        ),
        PaneRenderNode(
          nodeKey: 'title',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindText,
          semanticRole: 'heading',
          order: 0,
          text: 'Identity admission',
        ),
        PaneRenderNode(
          nodeKey: 'status',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindStatus,
          semanticRole: 'status',
          order: 1,
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'status_text',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.status',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: '0f345d90-ed11-57e3-b894-e0e234afc051',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'display_name',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindText,
          semanticRole: 'paragraph',
          order: 2,
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'display_name_text',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.display_name',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: 'ef122c87-2caa-5837-a182-ffd0d66cbd9e',
              transform: kPaneRenderStateTransformText,
              fallbackValue: 'No display name configured',
            ),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'public_handle',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindText,
          semanticRole: 'paragraph',
          order: 3,
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'public_handle_text',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.public_handle',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: '670f8092-f173-5a71-a3a3-551e28d0b1b4',
              transform: kPaneRenderStateTransformText,
              fallbackValue: 'No public handle configured',
            ),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'display_name_input',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindTextInput,
          semanticRole: 'input',
          order: 4,
          label: 'Display name',
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'display_name_value',
              targetProperty: kPaneRenderStateTargetValue,
              jsonPath: r'$.display_name',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: 'ef122c87-2caa-5837-a182-ffd0d66cbd9e',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'public_handle_input',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindTextInput,
          semanticRole: 'input',
          order: 5,
          label: 'Public handle',
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'public_handle_value',
              targetProperty: kPaneRenderStateTargetValue,
              jsonPath: r'$.public_handle',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: '670f8092-f173-5a71-a3a3-551e28d0b1b4',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'bio_input',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindTextInput,
          semanticRole: 'input',
          order: 6,
          label: 'Bio',
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'bio_value',
              targetProperty: kPaneRenderStateTargetValue,
              jsonPath: r'$.bio',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: '4f67b643-7f3c-5f1e-8120-212c219d6401',
              transform: kPaneRenderStateTransformText,
            ),
          ],
          styleTokens: <PaneStyleTokenRef>[
            PaneStyleTokenRef(tokenKey: 'input', tokenValue: 'multiline'),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'bio_preview',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindComponent,
          semanticRole: 'paragraph',
          order: 7,
          componentRef: 'aware.content.markdown_viewer',
          fallbackNodeKind: kPaneRenderNodeKindText,
          fallbackText: 'Bio preview unavailable',
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'bio_text',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.bio',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: '4f67b643-7f3c-5f1e-8120-212c219d6401',
              componentInputPortKey: 'markdown',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'submit',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindButton,
          semanticRole: 'action',
          order: 8,
          label: 'Admit identity',
          actionBindings: <PaneActionBinding>[
            PaneActionBinding(
              bindingKey: 'admit_identity',
              event: kPaneRenderActionEventActivate,
              actionKey: 'admit_identity',
              actionKind: kPaneRenderActionKindViewAction,
              label: 'Admit identity',
              receiptPolicy: 'show_receipt',
              inputBindings: <PaneInputBinding>[
                PaneInputBinding(
                  payloadPath: 'profile.display_name',
                  sourceNodeKey: 'display_name_input',
                ),
                PaneInputBinding(
                  payloadPath: 'profile.public_handle',
                  sourceNodeKey: 'public_handle_input',
                ),
                PaneInputBinding(
                  payloadPath: 'profile.bio',
                  sourceNodeKey: 'bio_input',
                ),
              ],
            ),
          ],
        ),
        PaneRenderNode(
          nodeKey: 'receipt',
          parentNodeKey: 'root',
          nodeKind: kPaneRenderNodeKindReceipt,
          semanticRole: 'receipt',
          order: 9,
          stateBindings: <PaneStateBinding>[
            PaneStateBinding(
              bindingKey: 'source_receipt',
              targetProperty: kPaneRenderStateTargetText,
              jsonPath: r'$.provenance.source_kind',
              stateModelId: '27dc7a7d-e719-5253-b72f-7e28158454c6',
              stateAttributeConfigId: '4b112a4b-14ae-57f5-9180-3cfe83360d1d',
              transform: kPaneRenderStateTransformText,
            ),
          ],
        ),
      ],
    ),
  ];
}

InterfacePackageRuntime buildAwareControlRenderSpecRuntime() {
  final renderComponentRegistryBuilder = RenderComponentRegistryBuilder();
  aware_content_render_components.registerRenderComponents(
    renderComponentRegistryBuilder,
  );
  return InterfacePackageRuntime(
    interfacePackageId: 'f6453e34-de79-5952-8581-eb671225f518',
    interfacePackageName: 'aware-control-interface',
    panePackageRegistry: PanePackageRegistry(),
    experienceKeys: const <String>['aware_control', 'aware_control_identity'],
    renderSpecs: buildAwareControlPaneRenderSpecs(),
    renderComponentRegistry: renderComponentRegistryBuilder.build(),
  );
}
