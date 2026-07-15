import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter/foundation.dart';

const String kPaneRenderNodeKindBox = 'box';
const String kPaneRenderNodeKindColumn = 'column';
const String kPaneRenderNodeKindDisclosure = 'disclosure';
const String kPaneRenderNodeKindField = 'field';
const String kPaneRenderNodeKindListItem = 'list_item';
const String kPaneRenderNodeKindMetric = 'metric';
const String kPaneRenderNodeKindRow = 'row';
const String kPaneRenderNodeKindScroll = 'scroll';
const String kPaneRenderNodeKindSectionHeader = 'section_header';
const String kPaneRenderNodeKindRepeat = 'repeat';
const String kPaneRenderNodeKindText = 'text';
const String kPaneRenderNodeKindStatus = 'status';
const String kPaneRenderNodeKindTextInput = 'text_input';
const String kPaneRenderNodeKindButton = 'button';
const String kPaneRenderNodeKindReceipt = 'receipt';
const String kPaneRenderNodeKindComponent = 'component';

const String kPaneRenderActionEventActivate = 'activate';
const String kPaneRenderActionKindApiEndpoint = 'api_endpoint';
const String kPaneRenderActionKindSdkOperation = 'sdk_operation';
const String kPaneRenderActionKindViewAction = 'view_action';
const String kPaneRenderActionKindAction = 'action';
const String kPaneRenderCapabilityKindRenderComponent = 'render_component';
const String kPaneRenderStateTargetText = 'text';
const String kPaneRenderStateTargetTone = 'tone';
const String kPaneRenderStateTargetVisible = 'visible';
const String kPaneRenderStateTargetEnabled = 'enabled';
const String kPaneRenderStateTargetValue = 'value';
const String kPaneRenderStateTargetItems = 'items';
const String kPaneRenderStateTargetMediaRef = 'media_ref';
const String kPaneRenderStateTransformRaw = 'raw';
const String kPaneRenderStateTransformText = 'text';
const String kPaneRenderStateTransformCount = 'count';
const String kPaneRenderStateTransformExists = 'exists';
const String kPaneRenderStateTransformPluralCount = 'plural_count';
const String kPaneRenderStateTransformNotEmpty = 'not_empty';
const String kPaneRenderStateTransformIsEmpty = 'is_empty';
const String _paneRenderSpecRootChildrenKey = '<root>';

final Expando<Map<String, List<PaneRenderNode>>> _paneRenderSpecChildrenCache =
    Expando<Map<String, List<PaneRenderNode>>>(
        'PaneRenderSpec.childrenByParent');

@immutable
class PaneRenderSpec {
  const PaneRenderSpec({
    required this.specId,
    required this.name,
    required this.specVersion,
    required this.paneKind,
    required this.rootNodeKey,
    required this.nodes,
    this.viewRef,
    this.projectionViewKey,
    this.stateModelId,
    this.rendererRequirements = const <PaneRendererCapabilityRequirement>[],
  });

  factory PaneRenderSpec.fromJson(Map<String, dynamic> json) {
    return PaneRenderSpec(
      specId: _stringValue(json['spec_id']) ?? _stringValue(json['specId'])!,
      name: _stringValue(json['name']) ?? '',
      specVersion:
          _stringValue(json['spec_version']) ?? _stringValue(json['version'])!,
      paneKind:
          _stringValue(json['pane_kind']) ?? _stringValue(json['paneKind'])!,
      rootNodeKey: _stringValue(json['root_node_key']) ??
          _stringValue(json['rootNodeKey'])!,
      viewRef: _stringValue(json['view_ref']) ?? _stringValue(json['viewRef']),
      projectionViewKey: _stringValue(json['projection_view_key']) ??
          _stringValue(json['projectionViewKey']),
      stateModelId: _stringValue(json['state_model_id']) ??
          _stringValue(json['stateModelId']),
      nodes: _mapList(json['nodes'], PaneRenderNode.fromJson),
      rendererRequirements: _mapList(
        json['renderer_requirements'] ?? json['rendererRequirements'],
        PaneRendererCapabilityRequirement.fromJson,
      ),
    );
  }

  final String specId;
  final String name;
  final String specVersion;
  final String paneKind;
  final String rootNodeKey;
  final String? viewRef;
  final String? projectionViewKey;
  final String? stateModelId;
  final List<PaneRenderNode> nodes;
  final List<PaneRendererCapabilityRequirement> rendererRequirements;

  bool matchesPane(InterfaceShellPaneMatch pane) {
    if (_normalized(pane.paneKind) != _normalized(paneKind)) {
      return false;
    }
    if (!_matchesOptional(viewRef, pane.viewRef)) {
      return false;
    }
    return _matchesOptional(projectionViewKey, pane.projectionViewKey);
  }

  List<PaneRenderNode> childrenOf(String? parentNodeKey) {
    final index = _paneRenderSpecChildrenCache[this] ??=
        _buildPaneRenderSpecChildrenIndex(this);
    final key = parentNodeKey == null
        ? _paneRenderSpecRootChildrenKey
        : _normalized(parentNodeKey);
    if (key == null) {
      return const <PaneRenderNode>[];
    }
    return index[key] ?? const <PaneRenderNode>[];
  }
}

Map<String, List<PaneRenderNode>> _buildPaneRenderSpecChildrenIndex(
  PaneRenderSpec spec,
) {
  final grouped = <String, List<PaneRenderNode>>{};
  for (final node in spec.nodes) {
    if (node.nodeKey == spec.rootNodeKey) {
      (grouped[_paneRenderSpecRootChildrenKey] ??= <PaneRenderNode>[]).add(
        node,
      );
    }
    final parentKey = _normalized(node.parentNodeKey);
    if (parentKey != null) {
      (grouped[parentKey] ??= <PaneRenderNode>[]).add(node);
    }
  }
  return Map<String, List<PaneRenderNode>>.unmodifiable(
    grouped.map((key, children) {
      final ordered = children.toList(growable: false)
        ..sort((a, b) {
          final byOrder = a.order.compareTo(b.order);
          if (byOrder != 0) {
            return byOrder;
          }
          return a.nodeKey.compareTo(b.nodeKey);
        });
      return MapEntry(key, List<PaneRenderNode>.unmodifiable(ordered));
    }),
  );
}

@immutable
class InterfaceShellPaneMatch {
  const InterfaceShellPaneMatch({
    required this.paneKind,
    this.viewRef,
    this.projectionViewKey,
  });

  final String paneKind;
  final String? viewRef;
  final String? projectionViewKey;
}

List<PaneRenderSpec> paneRenderSpecsFromInterfaceRuntimeState(
  InterfaceRuntimeState? runtime,
) {
  final dynamicStates = runtime?.dynamicPaneRenderSpecs ??
      const <InterfaceRuntimePaneRenderSpecState>[];
  return paneRenderSpecsFromRuntimePaneRenderSpecStates(dynamicStates);
}

List<PaneRenderSpec> paneRenderSpecsFromRuntimePaneRenderSpecStates(
  List<InterfaceRuntimePaneRenderSpecState> dynamicStates,
) {
  if (dynamicStates.isEmpty) {
    return const <PaneRenderSpec>[];
  }
  final renderSpecs = <PaneRenderSpec>[];
  for (final state in dynamicStates) {
    if (state.payload.isEmpty) {
      continue;
    }
    renderSpecs.add(PaneRenderSpec.fromJson(state.payload));
  }
  return List<PaneRenderSpec>.unmodifiable(renderSpecs);
}

@immutable
class PaneRenderNode {
  const PaneRenderNode({
    required this.nodeKey,
    required this.nodeKind,
    this.parentNodeKey,
    this.semanticRole,
    this.slotKey,
    this.order = 0,
    this.label,
    this.text,
    this.placeholder,
    this.componentRef,
    this.componentContractId,
    this.fallbackNodeKind,
    this.fallbackText,
    this.stateBindings = const <PaneStateBinding>[],
    this.actionBindings = const <PaneActionBinding>[],
    this.styleTokens = const <PaneStyleTokenRef>[],
  });

  factory PaneRenderNode.fromJson(Map<String, dynamic> json) {
    return PaneRenderNode(
      nodeKey: _stringValue(json['node_key']) ?? _stringValue(json['nodeKey'])!,
      nodeKind:
          _stringValue(json['node_kind']) ?? _stringValue(json['nodeKind'])!,
      parentNodeKey: _stringValue(json['parent_node_key']) ??
          _stringValue(json['parentNodeKey']),
      semanticRole: _stringValue(json['semantic_role']) ??
          _stringValue(json['semanticRole']),
      slotKey: _stringValue(json['slot_key']) ?? _stringValue(json['slotKey']),
      order: _intValue(json['order']) ?? 0,
      label: _stringValue(json['label']),
      text: _stringValue(json['text']),
      placeholder: _stringValue(json['placeholder']),
      componentRef: _stringValue(json['component_ref']) ??
          _stringValue(json['componentRef']),
      componentContractId: _stringValue(json['component_contract_id']) ??
          _stringValue(json['componentContractId']),
      fallbackNodeKind: _stringValue(json['fallback_node_kind']) ??
          _stringValue(json['fallbackNodeKind']),
      fallbackText: _stringValue(json['fallback_text']) ??
          _stringValue(json['fallbackText']),
      stateBindings: _mapList(
        json['state_bindings'] ?? json['stateBindings'],
        PaneStateBinding.fromJson,
      ),
      actionBindings: _mapList(
        json['action_bindings'] ?? json['actionBindings'],
        PaneActionBinding.fromJson,
      ),
      styleTokens: _mapList(
        json['style_tokens'] ?? json['styleTokens'],
        PaneStyleTokenRef.fromJson,
      ),
    );
  }

  final String nodeKey;
  final String nodeKind;
  final String? parentNodeKey;
  final String? semanticRole;
  final String? slotKey;
  final int order;
  final String? label;
  final String? text;
  final String? placeholder;
  final String? componentRef;
  final String? componentContractId;
  final String? fallbackNodeKind;
  final String? fallbackText;
  final List<PaneStateBinding> stateBindings;
  final List<PaneActionBinding> actionBindings;
  final List<PaneStyleTokenRef> styleTokens;

  PaneRenderNode withNodeKind(String nodeKind) {
    return PaneRenderNode(
      nodeKey: nodeKey,
      nodeKind: nodeKind,
      parentNodeKey: parentNodeKey,
      semanticRole: semanticRole,
      slotKey: slotKey,
      order: order,
      label: label,
      text: text,
      placeholder: placeholder,
      componentRef: componentRef,
      componentContractId: componentContractId,
      fallbackNodeKind: fallbackNodeKind,
      fallbackText: fallbackText,
      stateBindings: stateBindings,
      actionBindings: actionBindings,
      styleTokens: styleTokens,
    );
  }
}

@immutable
class PaneStateBinding {
  const PaneStateBinding({
    required this.bindingKey,
    required this.targetProperty,
    required this.jsonPath,
    this.stateModelId,
    this.stateAttributeConfigId,
    this.componentInputPortKey,
    this.transform = kPaneRenderStateTransformRaw,
    this.fallbackValue,
  });

  factory PaneStateBinding.fromJson(Map<String, dynamic> json) {
    return PaneStateBinding(
      bindingKey: _stringValue(json['binding_key']) ??
          _stringValue(json['bindingKey'])!,
      targetProperty: _stringValue(json['target_property']) ??
          _stringValue(json['targetProperty'])!,
      jsonPath:
          _stringValue(json['json_path']) ?? _stringValue(json['jsonPath'])!,
      stateModelId: _stringValue(json['state_model_id']) ??
          _stringValue(json['stateModelId']),
      stateAttributeConfigId: _stringValue(json['state_attribute_config_id']) ??
          _stringValue(json['stateAttributeConfigId']),
      componentInputPortKey: _stringValue(json['component_input_port_key']) ??
          _stringValue(json['componentInputPortKey']),
      transform:
          _stringValue(json['transform']) ?? kPaneRenderStateTransformRaw,
      fallbackValue: _stringValue(json['fallback_value']) ??
          _stringValue(json['fallbackValue']),
    );
  }

  final String bindingKey;
  final String targetProperty;
  final String jsonPath;
  final String? stateModelId;
  final String? stateAttributeConfigId;
  final String? componentInputPortKey;
  final String transform;
  final String? fallbackValue;
}

@immutable
class PaneActionBinding {
  const PaneActionBinding({
    required this.bindingKey,
    required this.event,
    required this.actionKey,
    this.actionKind,
    this.operationRef,
    this.sdkOperationId,
    this.paneConfigSdkOperationId,
    this.endpointRef,
    this.apiCapabilityEndpointId,
    this.paneConfigApiCapabilityEndpointId,
    this.componentActionPortKey,
    this.label,
    this.confirmationPolicy,
    this.optimisticPolicy,
    this.receiptPolicy,
    this.inputBindings = const <PaneInputBinding>[],
  });

  factory PaneActionBinding.fromJson(Map<String, dynamic> json) {
    final bindingKey = _stringValue(json['binding_key']) ??
        _stringValue(json['bindingKey']) ??
        _missingPaneActionBindingField(json, 'binding_key');
    final actionKey = _stringValue(json['action_key']) ??
        _stringValue(json['actionKey']) ??
        _missingPaneActionBindingField(json, 'action_key');
    return PaneActionBinding(
      bindingKey: bindingKey,
      event: _stringValue(json['event']) ?? kPaneRenderActionEventActivate,
      actionKey: actionKey,
      actionKind:
          _stringValue(json['action_kind']) ?? _stringValue(json['actionKind']),
      operationRef: _stringValue(json['operation_ref']) ??
          _stringValue(json['operationRef']) ??
          _stringValue(json['sdk_operation_ref']) ??
          _stringValue(json['sdkOperationRef']),
      sdkOperationId: _stringValue(json['sdk_operation_id']) ??
          _stringValue(json['sdkOperationId']),
      paneConfigSdkOperationId:
          _stringValue(json['pane_config_sdk_operation_id']) ??
              _stringValue(json['paneConfigSdkOperationId']),
      endpointRef: _stringValue(json['endpoint_ref']) ??
          _stringValue(json['endpointRef']) ??
          _stringValue(json['api_endpoint_ref']) ??
          _stringValue(json['apiEndpointRef']),
      apiCapabilityEndpointId:
          _stringValue(json['api_capability_endpoint_id']) ??
              _stringValue(json['apiCapabilityEndpointId']),
      paneConfigApiCapabilityEndpointId:
          _stringValue(json['pane_config_api_capability_endpoint_id']) ??
              _stringValue(json['paneConfigApiCapabilityEndpointId']),
      componentActionPortKey: _stringValue(json['component_action_port_key']) ??
          _stringValue(json['componentActionPortKey']),
      label: _stringValue(json['label']),
      confirmationPolicy: _stringValue(json['confirmation_policy']) ??
          _stringValue(json['confirmationPolicy']),
      optimisticPolicy: _stringValue(json['optimistic_policy']) ??
          _stringValue(json['optimisticPolicy']),
      receiptPolicy: _stringValue(json['receipt_policy']) ??
          _stringValue(json['receiptPolicy']),
      inputBindings: _mapList(
        json['input_bindings'] ?? json['inputBindings'],
        PaneInputBinding.fromJson,
      ),
    );
  }

  final String bindingKey;
  final String event;
  final String actionKey;
  final String? actionKind;
  final String? operationRef;
  final String? sdkOperationId;
  final String? paneConfigSdkOperationId;
  final String? endpointRef;
  final String? apiCapabilityEndpointId;
  final String? paneConfigApiCapabilityEndpointId;
  final String? componentActionPortKey;
  final String? label;
  final String? confirmationPolicy;
  final String? optimisticPolicy;
  final String? receiptPolicy;
  final List<PaneInputBinding> inputBindings;
}

Never _missingPaneActionBindingField(
  Map<String, dynamic> json,
  String fieldName,
) {
  final bindingKey = _stringValue(json['binding_key']) ??
      _stringValue(json['bindingKey']) ??
      '<unknown>';
  final extra = fieldName == 'action_key' &&
          (_stringValue(json['view_action_key']) ??
                  _stringValue(json['viewActionKey'])) !=
              null
      ? ' `view_action_key` is dispatch metadata; producers must also emit '
          'canonical `action_key`.'
      : '';
  throw FormatException(
    'PaneActionBinding `$bindingKey` is missing required `$fieldName`.$extra',
    json,
  );
}

@immutable
class PaneInputBinding {
  const PaneInputBinding({
    required this.payloadPath,
    this.sourceNodeKey,
    this.sourceJsonPath,
    this.literalValue,
  });

  factory PaneInputBinding.fromJson(Map<String, dynamic> json) {
    return PaneInputBinding(
      payloadPath: _stringValue(json['payload_path']) ??
          _stringValue(json['payloadPath'])!,
      sourceNodeKey: _stringValue(json['source_node_key']) ??
          _stringValue(json['sourceNodeKey']),
      sourceJsonPath: _stringValue(json['source_json_path']) ??
          _stringValue(json['sourceJsonPath']),
      literalValue: _stringValue(json['literal_value']) ??
          _stringValue(json['literalValue']),
    );
  }

  final String payloadPath;
  final String? sourceNodeKey;
  final String? sourceJsonPath;
  final String? literalValue;
}

@immutable
class PaneStyleTokenRef {
  const PaneStyleTokenRef({required this.tokenKey, this.tokenValue});

  factory PaneStyleTokenRef.fromJson(Map<String, dynamic> json) {
    return PaneStyleTokenRef(
      tokenKey:
          _stringValue(json['token_key']) ?? _stringValue(json['tokenKey'])!,
      tokenValue:
          _stringValue(json['token_value']) ?? _stringValue(json['tokenValue']),
    );
  }

  final String tokenKey;
  final String? tokenValue;
}

@immutable
class PaneRendererCapabilityRequirement {
  const PaneRendererCapabilityRequirement({
    required this.capabilityKind,
    required this.capabilityKey,
    this.isRequired = true,
  });

  factory PaneRendererCapabilityRequirement.fromJson(
    Map<String, dynamic> json,
  ) {
    return PaneRendererCapabilityRequirement(
      capabilityKind: _stringValue(json['capability_kind']) ??
          _stringValue(json['capabilityKind'])!,
      capabilityKey: _stringValue(json['capability_key']) ??
          _stringValue(json['capabilityKey'])!,
      isRequired: _boolValue(json['is_required']) ??
          _boolValue(json['isRequired']) ??
          true,
    );
  }

  final String capabilityKind;
  final String capabilityKey;
  final bool isRequired;
}

@immutable
class PaneRenderActionTarget {
  const PaneRenderActionTarget({
    required this.actionKey,
    required this.actionKind,
    this.operationRef,
    this.sdkOperationId,
    this.paneConfigSdkOperationId,
    this.endpointRef,
    this.apiCapabilityEndpointId,
    this.paneConfigApiCapabilityEndpointId,
  });

  factory PaneRenderActionTarget.fromBinding(PaneActionBinding binding) {
    final actionKey = binding.actionKey;
    final actionKind = _trimmedOrNull(binding.actionKind) ??
        _paneRenderActionKindForKey(actionKey);
    final operationRef = _trimmedOrNull(binding.operationRef) ??
        _prefixedActionTargetRef(actionKey, 'sdk:');
    final endpointRef = _trimmedOrNull(binding.endpointRef) ??
        _prefixedActionTargetRef(actionKey, 'api:');
    return PaneRenderActionTarget(
      actionKey: actionKey,
      actionKind: actionKind,
      operationRef: operationRef,
      sdkOperationId: _trimmedOrNull(binding.sdkOperationId),
      paneConfigSdkOperationId: _trimmedOrNull(
        binding.paneConfigSdkOperationId,
      ),
      endpointRef: endpointRef,
      apiCapabilityEndpointId: _trimmedOrNull(binding.apiCapabilityEndpointId),
      paneConfigApiCapabilityEndpointId: _trimmedOrNull(
        binding.paneConfigApiCapabilityEndpointId,
      ),
    );
  }

  final String actionKey;
  final String actionKind;
  final String? operationRef;
  final String? sdkOperationId;
  final String? paneConfigSdkOperationId;
  final String? endpointRef;
  final String? apiCapabilityEndpointId;
  final String? paneConfigApiCapabilityEndpointId;

  bool get isSdkOperation => actionKind == kPaneRenderActionKindSdkOperation;
  bool get isApiEndpoint => actionKind == kPaneRenderActionKindApiEndpoint;
}

@immutable
class PaneRenderActionInvocation {
  PaneRenderActionInvocation({
    required this.paneContext,
    required this.actionBinding,
    required this.payload,
    PaneRenderActionTarget? actionTarget,
  }) : actionTarget =
            actionTarget ?? PaneRenderActionTarget.fromBinding(actionBinding);

  final PaneContext paneContext;
  final PaneActionBinding actionBinding;
  final PaneRenderActionTarget actionTarget;
  final Map<String, dynamic> payload;

  String get actionKey => actionTarget.actionKey;
  String get actionKind => actionTarget.actionKind;
  String? get operationRef => actionTarget.operationRef;
  String? get sdkOperationId => actionTarget.sdkOperationId;
  String? get paneConfigSdkOperationId => actionTarget.paneConfigSdkOperationId;
  String? get endpointRef => actionTarget.endpointRef;
  String? get apiCapabilityEndpointId => actionTarget.apiCapabilityEndpointId;
  String? get paneConfigApiCapabilityEndpointId =>
      actionTarget.paneConfigApiCapabilityEndpointId;
}

typedef PaneRenderActionInvoker = Future<void> Function(
    PaneRenderActionInvocation invocation);

Object? paneRenderResolveStatePath(
  InterfaceMaterializedPaneState? materializedState,
  String path, {
  Object? item,
  Object? parentItem,
  int? itemIndex,
  int? parentIndex,
}) {
  if (materializedState == null) {
    return null;
  }
  final normalized = path.trim().replaceFirst(RegExp(r'^\$\.'), '');
  if (normalized.isEmpty || normalized == r'$') {
    return materializedState.state;
  }
  Object? current = materializedState.state;
  for (final segment in normalized.split('.')) {
    if (segment == 'item') {
      current = item;
    } else if (segment == 'parent') {
      current = parentItem;
    } else if (segment == 'item_index') {
      current = itemIndex;
    } else if (segment == 'parent_index') {
      current = parentIndex;
    } else if (current is Map<String, dynamic>) {
      current = current[segment];
    } else if (current is Map) {
      current = current[segment];
    } else if (current is List) {
      final index = int.tryParse(segment);
      if (index == null || index < 0 || index >= current.length) {
        return null;
      }
      current = current[index];
    } else {
      return null;
    }
  }
  return current;
}

Object? paneRenderApplyStateTransform(PaneStateBinding binding, Object? value) {
  final transformed = switch (binding.transform) {
    kPaneRenderStateTransformText => _displayString(value),
    kPaneRenderStateTransformCount => _displayCount(value),
    kPaneRenderStateTransformPluralCount => _displayPluralCount(binding, value),
    kPaneRenderStateTransformExists => value != null,
    kPaneRenderStateTransformNotEmpty => _isNotEmptyValue(value),
    kPaneRenderStateTransformIsEmpty => _isEmptyValue(value),
    kPaneRenderStateTransformRaw => value,
    _ => throw UnsupportedError(
        'Unsupported PaneRender state transform: ${binding.transform}',
      ),
  };
  return transformed ?? binding.fallbackValue;
}

String? _displayCount(Object? value) {
  if (value == null) {
    return null;
  }
  if (value is Iterable) {
    return value.length.toString();
  }
  if (value is Map) {
    return value.length.toString();
  }
  if (value is String) {
    return value.trim().isEmpty ? null : '1';
  }
  return '1';
}

String? _displayPluralCount(PaneStateBinding binding, Object? value) {
  final count = _countValue(value);
  if (count == null) {
    return null;
  }
  final labels = _pluralLabelsFromFallback(binding.fallbackValue);
  return '$count ${count == 1 ? labels.singular : labels.plural}';
}

int? _countValue(Object? value) {
  if (value == null) {
    return null;
  }
  if (value is Iterable) {
    return value.length;
  }
  if (value is Map) {
    return value.length;
  }
  if (value is String) {
    return value.trim().isEmpty ? null : 1;
  }
  return 1;
}

({String singular, String plural}) _pluralLabelsFromFallback(String? fallback) {
  final tokens = fallback?.trim().split(RegExp(r'\s+')) ?? const <String>[];
  final plural = tokens.isEmpty || tokens.last.isEmpty ? 'items' : tokens.last;
  if (plural.endsWith('ies') && plural.length > 3) {
    return (
      singular: '${plural.substring(0, plural.length - 3)}y',
      plural: plural,
    );
  }
  if (plural.endsWith('s') && plural.length > 1) {
    return (singular: plural.substring(0, plural.length - 1), plural: plural);
  }
  return (singular: plural, plural: '${plural}s');
}

bool _isEmptyValue(Object? value) {
  if (value == null) {
    return true;
  }
  if (value is String) {
    return value.trim().isEmpty;
  }
  if (value is Iterable) {
    return value.isEmpty;
  }
  if (value is Map) {
    return value.isEmpty;
  }
  return false;
}

bool _isNotEmptyValue(Object? value) {
  return !_isEmptyValue(value);
}

List<T> _mapList<T>(
  Object? raw,
  T Function(Map<String, dynamic> json) fromJson,
) {
  if (raw is! List) {
    return List<T>.empty(growable: false);
  }
  return List<T>.unmodifiable(
    raw.whereType<Map>().map((item) => fromJson(item.cast<String, dynamic>())),
  );
}

String? _displayString(Object? value) {
  if (value == null) {
    return null;
  }
  final text = value.toString().trim();
  return text.isEmpty ? null : text;
}

String _paneRenderActionKindForKey(String actionKey) {
  if (actionKey.startsWith('sdk:')) {
    return kPaneRenderActionKindSdkOperation;
  }
  if (actionKey.startsWith('api:')) {
    return kPaneRenderActionKindApiEndpoint;
  }
  return kPaneRenderActionKindAction;
}

String? _prefixedActionTargetRef(String actionKey, String prefix) {
  if (!actionKey.startsWith(prefix)) {
    return null;
  }
  return _trimmedOrNull(actionKey.substring(prefix.length));
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

String? _stringValue(Object? value) {
  if (value is! String) {
    return null;
  }
  final trimmed = value.trim();
  return trimmed.isEmpty ? null : trimmed;
}

int? _intValue(Object? value) {
  if (value is int) {
    return value;
  }
  if (value is num) {
    return value.toInt();
  }
  return int.tryParse('${value ?? ''}'.trim());
}

bool? _boolValue(Object? value) {
  if (value is bool) {
    return value;
  }
  final normalized = '${value ?? ''}'.trim().toLowerCase();
  if (normalized == 'true') {
    return true;
  }
  if (normalized == 'false') {
    return false;
  }
  return null;
}

bool _matchesOptional(String? expected, String? actual) {
  final normalizedExpected = _normalized(expected);
  if (normalizedExpected == null) {
    return true;
  }
  return normalizedExpected == _normalized(actual);
}

String? _normalized(String? value) {
  final trimmed = value?.trim().toLowerCase();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
