import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

void main() {
  test('builds renderer capabilities from compiled interface runtime', () {
    final panePackageId = UuidValue.fromString(
      '99999999-9999-4999-8999-999999999999',
    );
    final registry = PanePackageRegistry()
      ..registerPanePackage(
        panePackageId: panePackageId,
        panePackageName: 'identity-admission-pane',
        paneKind: 'identity_admission',
        factory: (_) => const SizedBox.shrink(),
        capabilities: const runtime.PaneCapabilities(),
      );
    final packageRuntime = InterfacePackageRuntime(
      interfacePackageId: '33333333-3333-4333-8333-333333333333',
      interfacePackageName: 'aware-control-interface',
      panePackageRegistry: registry,
      experienceKeys: const <String>['aware_control_identity', ''],
      sectionRepresentations:
          const <InterfacePackageRuntimeSectionRepresentation>[
            InterfacePackageRuntimeSectionRepresentation(
              representationId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
              windowKey: 'main',
              layoutKey: 'coordination_center',
              sectionKey: 'workspace',
              paneName: 'identity',
              paneKind: 'identity_admission',
              label: 'Identity',
              observableId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
              viewRef: 'aware_identity.profile.home.v1',
              projectionViewKey: 'profile.home.v1',
            ),
          ],
      viewStateDecoderRegistry:
          InterfaceViewStateDecoderRegistry.fromDecoderMaps(
            <Map<String, InterfaceViewStateDecoder>>[
              <String, InterfaceViewStateDecoder>{
                'aware_identity.profile.home.v1': FakeViewState.fromJson,
              },
            ],
          ),
    );

    final capabilities = buildInterfaceRendererCapabilities(
      runtime: packageRuntime,
      rendererId: 'flutter-test',
      rendererVersion: '0.1.0',
      reportedAt: DateTime.utc(2026, 5, 7),
    );

    expect(capabilities.rendererId, 'flutter-test');
    expect(capabilities.rendererKind, 'flutter');
    expect(capabilities.rendererVersion, '0.1.0');
    expect(
      capabilities.interfacePackageId?.uuid,
      '33333333-3333-4333-8333-333333333333',
    );
    expect(capabilities.interfacePackageName, 'aware-control-interface');
    expect(capabilities.experienceKeys, <String>['aware_control_identity']);
    expect(capabilities.panePackages.single.panePackageId, panePackageId);
    expect(capabilities.panePackages.single.paneKind, 'identity_admission');
    expect(capabilities.viewCapabilities.single.hasDecoder, isTrue);
    expect(
      capabilities.viewCapabilities.single.projectionViewKey,
      'profile.home.v1',
    );
    expect(capabilities.cache?.storeKind, 'memory');
    expect(capabilities.cache?.supportsNamespaceReplace, isTrue);
    expect(capabilities.cache?.supportsPersistentStorage, isFalse);
    expect(capabilities.cache?.supportsCursorLookup, isTrue);
    expect(capabilities.reportedAt, '2026-05-07T00:00:00.000Z');
  });
}

class FakeViewState {
  const FakeViewState({required this.label});

  factory FakeViewState.fromJson(Map<String, dynamic> json) {
    return FakeViewState(label: json['label'] as String? ?? '');
  }

  final String label;
}
