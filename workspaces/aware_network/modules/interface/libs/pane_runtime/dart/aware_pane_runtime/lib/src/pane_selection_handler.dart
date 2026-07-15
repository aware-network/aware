import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;

import 'pane_kind.dart';
import 'pane_selection_context.dart';

typedef ProviderReader = T Function<T>(ProviderListenable<T> provider);

abstract class PaneSelectionHandler {
  const PaneSelectionHandler();

  PaneKey get paneKind;

  Future<void> handle({
    required ProviderReader read,
    required runtime.PaneSelectionPayload<Object?> selection,
    PaneSelectionContext? selectionContext,
  });
}
