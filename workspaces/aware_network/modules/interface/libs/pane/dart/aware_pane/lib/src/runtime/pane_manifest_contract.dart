import '../runtime/pane_key.dart';

/// Opaque branch reference passed between host and shared runtime.
class PaneBranchContext {
  const PaneBranchContext({
    required this.branchId,
    this.threadId,
    this.metadata = const <String, Object?>{},
  });

  final String branchId;
  final String? threadId;
  final Map<String, Object?> metadata;
}

/// Contract for panes that materialise manifest data.
abstract class PaneManifestAdapterContract<TPayload> {
  PaneKey get paneKey;

  Future<TPayload?> load(PaneBranchContext context);

  Future<TPayload> build(PaneBranchContext context);

  Future<void> save(PaneBranchContext context, TPayload payload);

  Future<TPayload> ensure(PaneBranchContext context) async {
    final existing = await load(context);
    if (existing != null) {
      return existing;
    }
    final rebuilt = await build(context);
    await save(context, rebuilt);
    return rebuilt;
  }
}
