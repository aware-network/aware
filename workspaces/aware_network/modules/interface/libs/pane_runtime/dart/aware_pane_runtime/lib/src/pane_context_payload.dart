import 'pane_kind.dart';

abstract class PaneContextPayload {
  PaneKey get paneKind;
  String? get displayName;
  String? get secondaryLabel;
}
