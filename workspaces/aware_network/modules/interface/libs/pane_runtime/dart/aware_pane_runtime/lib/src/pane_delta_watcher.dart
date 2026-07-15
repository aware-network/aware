import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:aware_pane/aware_pane.dart' as runtime;

import 'pane_kind.dart';

typedef PaneProviderReader = T Function<T>(ProviderListenable<T> provider);

abstract class PaneDeltaWatcher<TPayload> {
  const PaneDeltaWatcher();

  PaneKey get paneKind;

  Stream<runtime.PaneDeltaEvent> watch({
    required PaneProviderReader read,
    required runtime.PaneWatcherInput input,
  });

  Future<runtime.PaneHydrationDelta<TPayload>> resolve({
    required PaneProviderReader read,
    required runtime.PaneDeltaEvent event,
  });
}
