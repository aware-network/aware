import 'pane_context_payload.dart';
import 'pane_kind.dart';

abstract class PaneManifestDecoder {
  PaneKey get paneKind;
  PaneContextPayload? decode(dynamic payload);
}
