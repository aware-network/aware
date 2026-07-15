import 'package:aware_shell/aware_shell.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('decodes materialized view state by view ref', () {
    final registry = InterfaceViewStateDecoderRegistry.fromDecoderMaps(
      <Map<String, InterfaceViewStateDecoder>>[
        <String, InterfaceViewStateDecoder>{
          'aware_test.identity.profile.v1': FakeViewState.fromJson,
        },
      ],
    );

    final result = registry.decodeMaterialized<FakeViewState>(
      materializedState: _materializedState(
        state: <String, dynamic>{'label': 'Ready'},
      ),
      viewRef: 'aware_test.identity.profile.v1',
      viewKey: 'identity.profile.v1',
    );

    expect(result.status, InterfaceViewStateDecodeStatus.decoded);
    expect(result.value?.label, 'Ready');
    expect(result.decoderKey, 'aware_test.identity.profile.v1');
  });

  test('decodes materialized view state by view key fallback', () {
    final registry = InterfaceViewStateDecoderRegistry.fromDecoderMaps(
      <Map<String, InterfaceViewStateDecoder>>[
        <String, InterfaceViewStateDecoder>{
          'identity.profile.v1': FakeViewState.fromJson,
        },
      ],
    );

    final result = registry.decodeMaterialized<FakeViewState>(
      materializedState: _materializedState(
        state: <String, dynamic>{'label': 'Fallback'},
      ),
      viewKey: 'identity.profile.v1',
    );

    expect(result.status, InterfaceViewStateDecodeStatus.decoded);
    expect(result.value?.label, 'Fallback');
    expect(result.decoderKey, 'identity.profile.v1');
  });

  test('fails closed when materialized state is missing', () {
    const registry = InterfaceViewStateDecoderRegistry.empty();

    final result = registry.decodeMaterialized<FakeViewState>(
      materializedState: null,
      viewRef: 'aware_test.identity.profile.v1',
    );

    expect(
      result.status,
      InterfaceViewStateDecodeStatus.missingMaterializedState,
    );
    expect(result.value, isNull);
  });

  test('fails closed when decoder is missing', () {
    const registry = InterfaceViewStateDecoderRegistry.empty();

    final result = registry.decodeMaterialized<FakeViewState>(
      materializedState: _materializedState(
        state: <String, dynamic>{'label': 'Ready'},
      ),
      viewRef: 'aware_test.identity.profile.v1',
    );

    expect(result.status, InterfaceViewStateDecodeStatus.missingDecoder);
    expect(result.value, isNull);
  });

  test('fails closed when payload cannot be decoded', () {
    final registry = InterfaceViewStateDecoderRegistry.fromDecoderMaps(
      <Map<String, InterfaceViewStateDecoder>>[
        <String, InterfaceViewStateDecoder>{
          'aware_test.identity.profile.v1': FakeViewState.fromJson,
        },
      ],
    );

    final result = registry.decodeMaterialized<FakeViewState>(
      materializedState: _materializedState(
        state: <String, dynamic>{'label': 42},
      ),
      viewRef: 'aware_test.identity.profile.v1',
    );

    expect(result.status, InterfaceViewStateDecodeStatus.invalidPayload);
    expect(result.value, isNull);
    expect(result.error, isA<TypeError>());
  });
}

InterfaceMaterializedPaneState _materializedState({
  required Map<String, dynamic> state,
}) {
  return InterfaceMaterializedPaneState(
    paneStateKey: 'main:layout:section:identity:test-pane:hash',
    windowKey: 'main',
    layoutKey: 'layout',
    sectionKey: 'section',
    paneKind: 'identity',
    status: 'materialized',
    state: state,
    provenance: const <String, dynamic>{
      'view_ref': 'aware_test.identity.profile.v1',
      'projection_view_key': 'identity.profile.v1',
    },
  );
}

class FakeViewState {
  const FakeViewState({required this.label});

  factory FakeViewState.fromJson(Map<String, dynamic> json) {
    return FakeViewState(label: json['label'] as String);
  }

  final String label;
}
