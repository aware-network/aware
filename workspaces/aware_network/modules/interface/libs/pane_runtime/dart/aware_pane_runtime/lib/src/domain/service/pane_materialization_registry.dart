import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logging/logging.dart';

import '../../pane_kind.dart';
import '../runtime/pane_materialization_mode.dart';

typedef PaneMaterializerProvider<T> = ProviderListenable<T>;

class PaneMaterializationRegistry {
  PaneMaterializationRegistry();

  final Logger _logger = Logger('PaneMaterializationRegistry');

  final Map<
    PaneKey,
    Map<PaneMaterializationMode, PaneMaterializerProvider<dynamic>>
  >
  _providers = {};

  void register<T>(
    PaneKey kind,
    PaneMaterializationMode mode,
    PaneMaterializerProvider<T> provider,
  ) {
    final entries = _providers.putIfAbsent(
      kind,
      () => <PaneMaterializationMode, PaneMaterializerProvider<dynamic>>{},
    );

    if (entries.containsKey(mode)) {
      _logger.warning(
        'Overwriting materialization provider for ${kind.name} (${mode.label}).',
      );
    }

    entries[mode] = provider;
    _logger.fine(
      'Registered materialization provider for ${kind.name} in ${mode.label} mode.',
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

  PaneMaterializerProvider<T> providerFor<T>(
    PaneKey kind,
    PaneMaterializationMode mode,
  ) {
    final entries = _providers[kind];
    if (entries == null || !entries.containsKey(mode)) {
      throw StateError(
        'No materialization provider registered for pane ${kind.name} in '
        '${mode.label} mode. Register one via PaneMaterializationRegistry.',
      );
    }

    return entries[mode]! as PaneMaterializerProvider<T>;
  }

  T resolve<T>(PaneKey kind, PaneMaterializationMode mode, Ref ref) {
    final provider = providerFor<T>(kind, mode);
    return ref.watch(provider);
  }

  void clear() {
    _providers.clear();
  }
}
