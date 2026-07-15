import 'package:aware_pane/aware_pane.dart';
import 'package:flutter_test/flutter_test.dart';

class _RecordingSelectionHandler
    extends PaneSelectionHandler<Map<String, dynamic>> {
  _RecordingSelectionHandler(String paneKey) : super(paneKey: paneKey);

  PaneContext? lastContext;
  Map<String, dynamic>? lastPayload;
  Map<String, Object?>? lastMetadata;

  @override
  Future<void> handle(
    PaneContext paneContext,
    Map<String, dynamic> payload,
    Map<String, Object?> metadata,
  ) async {
    lastContext = paneContext;
    lastPayload = payload;
    lastMetadata = metadata;
  }
}

void main() {
  group('PaneSelectionHandler', () {
    test('proxy forwards metadata and payload', () async {
      final handler = _RecordingSelectionHandler('demo');

      await handler.handle(
        const PaneContext(
          paneKey: 'demo',
          parameters: {'foo': 'bar'},
          metadata: {'projectId': 'project-1'},
        ),
        const {'baz': 42},
        const {'projectId': 'project-1'},
      );

      expect(handler.lastContext, isNotNull);
      expect(handler.lastContext!.metadata['projectId'], 'project-1');
      expect(handler.lastContext!.parameters['foo'], 'bar');
      expect(handler.lastPayload, const {'baz': 42});
      expect(handler.lastMetadata, const {'projectId': 'project-1'});
    });
  });
}
