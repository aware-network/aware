import 'package:aware_pane/aware_pane.dart' as runtime;

import '../../pane_delta_watcher.dart';
import '../../pane_kind.dart';
import '../../pane_manifest_adapter.dart';
import '../../pane_manifest_decoder.dart';
import '../../pane_selection_handler.dart';
import '../../pane_system.dart';
import '../runtime/pane_materialization_mode.dart';
import '../service/pane_function_registry.dart';
import '../service/pane_materialization_registry.dart';
import '../service/pane_registry.dart';
import 'pane_factory.dart';

class PaneMaterializationEntry {
  const PaneMaterializationEntry({required this.mode, required this.provider});

  final PaneMaterializationMode mode;
  final PaneMaterializerProvider<dynamic> provider;
}

class PaneMaterialisationConfig {
  const PaneMaterialisationConfig({required this.entries});

  PaneMaterialisationConfig.single({
    required PaneMaterializationMode mode,
    required PaneMaterializerProvider<dynamic> provider,
  }) : entries = [PaneMaterializationEntry(mode: mode, provider: provider)];

  final List<PaneMaterializationEntry> entries;

  bool get isEmpty => entries.isEmpty;
}

class PaneFunctionEntry {
  const PaneFunctionEntry({required this.mode, required this.provider});

  final PaneMaterializationMode mode;
  final PaneFunctionProvider<dynamic> provider;
}

class PaneFunctionConfig {
  const PaneFunctionConfig({required this.entries});

  PaneFunctionConfig.single({
    required PaneMaterializationMode mode,
    required PaneFunctionProvider<dynamic> provider,
  }) : entries = [PaneFunctionEntry(mode: mode, provider: provider)];

  final List<PaneFunctionEntry> entries;

  bool get isEmpty => entries.isEmpty;
}

class PaneModule {
  const PaneModule({
    required this.kind,
    required this.factory,
    required this.capabilities,
    this.displayInfo,
    this.agreement,
    this.manifestAdapter,
    this.manifestDecoder,
    this.selectionHandler,
    this.deltaWatcher,
    this.opgBinding,
    this.materialisation = const [],
    this.functions = const [],
  });

  final PaneKey kind;
  final PaneFactory factory;
  final runtime.PaneCapabilities capabilities;
  final PaneDisplayInfo? displayInfo;
  final Object? agreement;
  final PaneManifestAdapter<dynamic>? manifestAdapter;
  final PaneManifestDecoder? manifestDecoder;
  final PaneSelectionHandler? selectionHandler;
  final PaneDeltaWatcher<dynamic>? deltaWatcher;
  final PaneOpgBinding? opgBinding;
  final List<PaneMaterialisationConfig> materialisation;
  final List<PaneFunctionConfig> functions;
}

class PaneManifestRegistrations {
  const PaneManifestRegistrations({
    required this.materializationRegistry,
    required this.functionRegistry,
  });

  final PaneMaterializationRegistry materializationRegistry;
  final PaneFunctionRegistry functionRegistry;
}
