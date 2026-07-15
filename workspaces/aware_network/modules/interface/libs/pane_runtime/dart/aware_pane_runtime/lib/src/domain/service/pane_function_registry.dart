import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logging/logging.dart';

import '../../pane_kind.dart';
import '../runtime/pane_materialization_mode.dart';

typedef PaneFunctionProvider<T> = ProviderListenable<T>;

class PaneFunctionRegistry {
  PaneFunctionRegistry();

  final Logger _logger = Logger('PaneFunctionRegistry');

  final Map<
    PaneKey,
    Map<PaneMaterializationMode, PaneFunctionProvider<dynamic>>
  >
  _providers = {};

  void register<T>(
    PaneKey kind,
    PaneMaterializationMode mode,
    PaneFunctionProvider<T> provider,
  ) {
    final entries = _providers.putIfAbsent(
      kind,
      () => <PaneMaterializationMode, PaneFunctionProvider<dynamic>>{},
    );

    if (entries.containsKey(mode)) {
      _logger.warning(
        'Overwriting function provider for ${kind.name} (${mode.label}).',
      );
    }

    entries[mode] = provider;
    _logger.fine(
      'Registered function provider for ${kind.name} in ${mode.label} mode.',
    );
  }

  bool isRegistered(PaneKey kind, PaneMaterializationMode mode) {
    return _providers[kind]?.containsKey(mode) ?? false;
  }

  void unregister(PaneKey kind, PaneMaterializationMode mode) {
    final entries = _providers[kind];
    if (entries == null) {
      return;
    }

    entries.remove(mode);
    if (entries.isEmpty) {
      _providers.remove(kind);
    }
  }

  PaneFunctionProvider<T> providerFor<T>(
    PaneKey kind,
    PaneMaterializationMode mode,
  ) {
    final entries = _providers[kind];
    if (entries == null || !entries.containsKey(mode)) {
      throw StateError(
        'No function provider registered for pane ${kind.name} in '
        '${mode.label} mode. Register one via PaneFunctionRegistry.',
      );
    }

    return entries[mode]! as PaneFunctionProvider<T>;
  }

  T resolve<T>(PaneKey kind, PaneMaterializationMode mode, Ref ref) {
    final provider = providerFor<T>(kind, mode);
    return ref.watch(provider);
  }

  void clear() {
    _providers.clear();
  }
}
