import 'dart:async';

import 'pane_kind.dart';
import 'pane_manifest_runtime.dart';

abstract class PaneManifestAdapter<TPayload> {
  PaneKey get paneKind;

  Future<PaneManifestBundle<TPayload>?> load({required String threadDirectory});

  Future<List<PaneManifestBundle<TPayload>>> loadAll({
    required String threadDirectory,
  }) async {
    final bundle = await load(threadDirectory: threadDirectory);
    if (bundle == null) {
      return const [];
    }
    return [bundle];
  }

  Future<PaneManifestBundle<TPayload>> build({
    required PaneThreadSnapshot snapshot,
    required String threadDirectory,
  });

  Future<void> save({
    required String threadDirectory,
    required PaneManifestBundle<TPayload> manifest,
  });

  Future<PaneManifestBundle<TPayload>> ensure({
    required PaneThreadSnapshot snapshot,
    required String threadDirectory,
    bool persistIfMissing = true,
  }) async {
    final existing = await load(threadDirectory: threadDirectory);
    if (existing != null) {
      return existing;
    }

    final rebuilt = await build(
      snapshot: snapshot,
      threadDirectory: threadDirectory,
    );

    if (persistIfMissing) {
      await save(threadDirectory: threadDirectory, manifest: rebuilt);
    }

    return rebuilt;
  }
}
