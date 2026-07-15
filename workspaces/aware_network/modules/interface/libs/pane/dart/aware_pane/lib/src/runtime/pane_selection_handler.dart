import 'pane_context.dart';
import 'pane_key.dart';

/// Host-provided selection handler that reacts to context changes.
abstract class PaneSelectionHandler<TPayload> {
  const PaneSelectionHandler({required this.paneKey});

  final PaneKey paneKey;

  Future<void> handle(
    PaneContext paneContext,
    TPayload payload,
    Map<String, Object?> metadata,
  );
}
