import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logging/logging.dart';

import '../../pane_kind.dart';
import '../../pane_agreement.dart';
import '../model/pane_module.dart';
import '../service/pane_registry.dart';

typedef RuntimeProviderReader = T Function<T>(ProviderListenable<T> provider);

class PaneRuntime {
  PaneRuntime({required PaneRegistry registry})
    : _registry = registry,
      _logger = Logger('PaneRuntime');

  final PaneRegistry _registry;
  final Logger _logger;

  void initialize({
    required List<PaneModule> modules,
    required RuntimeProviderReader providerReader,
    required PaneManifestRegistrations manifestRegistrations,
  }) {
    _logger.info('PaneRuntime initializing ${modules.length} pane modules.');

    _registry.setProviderReader(providerReader);

    // Register manifest adapters and decoders first so panes can hydrate.
    for (final module in modules) {
      final manifestAdapter = module.manifestAdapter;
      if (manifestAdapter != null) {
        _registry.registerManifestAdapter<dynamic>(manifestAdapter);
      }

      final manifestDecoder = module.manifestDecoder;
      if (manifestDecoder != null) {
        _registry.registerManifestDecoder(manifestDecoder);
      }
    }

    // Register selection handlers and delta watchers.
    for (final module in modules) {
      final selectionHandler = module.selectionHandler;
      if (selectionHandler != null) {
        _registry.registerSelectionHandler(selectionHandler);
      }

      final deltaWatcher = module.deltaWatcher;
      if (deltaWatcher != null) {
        _registry.registerDeltaWatcher<dynamic>(
          kind: module.kind,
          watcher: deltaWatcher,
        );
      }
    }

    // Register materialization providers.
    for (final module in modules) {
      if (module.materialisation.isEmpty) {
        continue;
      }
      for (final config in module.materialisation) {
        for (final entry in config.entries) {
          if (!manifestRegistrations.materializationRegistry.isRegistered(
            module.kind,
            entry.mode,
          )) {
            manifestRegistrations.materializationRegistry.register(
              module.kind,
              entry.mode,
              entry.provider,
            );
          }
        }
      }
    }

    // Register function providers.
    for (final module in modules) {
      if (module.functions.isEmpty) {
        continue;
      }
      for (final config in module.functions) {
        for (final entry in config.entries) {
          if (!manifestRegistrations.functionRegistry.isRegistered(
            module.kind,
            entry.mode,
          )) {
            manifestRegistrations.functionRegistry.register(
              module.kind,
              entry.mode,
              entry.provider,
            );
          }
        }
      }
    }

    // Register panes + agreements + display info.
    for (final module in modules) {
      final agreement = module.agreement;
      _registry.registerPane(
        kind: module.kind,
        factory: module.factory,
        capabilities: module.capabilities,
        agreement: agreement is PaneAgreement ? agreement : null,
        displayInfo: module.displayInfo,
      );

      final opgBinding = module.opgBinding;
      if (opgBinding != null) {
        final existing = _registry.paneOpgBindingFor(module.kind);
        if (existing == null) {
          _registry.registerOpgBinding(module.kind, opgBinding);
        } else if (existing.opgName != opgBinding.opgName) {
          _logger.warning(
            'Pane ${module.kind.name} already bound to ${existing.opgName}; '
            'new binding ${opgBinding.opgName} ignored.',
          );
        }
      }
    }

    _registry.markReady();
    _logger.info('PaneRuntime initialization complete.');
  }

  PaneRegistry get registry => _registry;
}
