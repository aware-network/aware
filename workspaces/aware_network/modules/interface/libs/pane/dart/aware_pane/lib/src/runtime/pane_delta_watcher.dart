import 'pane_key.dart';
import 'pane_manifest_contract.dart';

/// Identifies the type of change emitted by a pane watcher.
enum PaneDeltaKind { added, updated, removed }

/// Host-provided context for starting a pane delta watcher.
///
/// The map-based structure keeps the contract agnostic of host-domain models
/// (e.g., threads, processes). Hosts provide whatever identifiers the watcher
/// needs via `parameters` and optional `metadata`.
class PaneWatcherInput {
  const PaneWatcherInput({
    required this.parameters,
    this.metadata = const <String, Object?>{},
  });

  /// Arbitrary parameters supplied by the host (e.g., pane instance config).
  final Map<String, Object?> parameters;

  /// Optional metadata channel for hosts to pass auxiliary identifiers.
  final Map<String, Object?> metadata;
}

/// Lightweight event emitted by pane watchers when a potential change occurs.
///
/// The watcher does not perform expensive materialisation; it simply signals
/// that the branch identified by [branchContext] has changed in the specified
/// [kind]. Hosts may use the metadata to optimise debouncing or batching.
class PaneDeltaEvent {
  const PaneDeltaEvent({
    required this.kind,
    required this.branchContext,
    this.metadata = const <String, Object?>{},
  });

  final PaneDeltaKind kind;
  final PaneBranchContext branchContext;
  final Map<String, Object?> metadata;
}

/// Result of resolving a delta event into a materialisable payload.
///
/// The payload type [TPayload] matches the pane's manifest adapter contract.
/// Hosts can use [metadata] for implementation-specific hints (e.g., file
/// paths, commit hashes) while keeping the runtime contract generic.
class PaneHydrationDelta<TPayload> {
  const PaneHydrationDelta({
    required this.kind,
    required this.branchContext,
    this.payload,
    this.metadata = const <String, Object?>{},
  });

  final PaneDeltaKind kind;
  final PaneBranchContext branchContext;
  final TPayload? payload;
  final Map<String, Object?> metadata;
}

/// Contract implemented by panes that support incremental updates.
///
/// Implementations stay host-agnostic: they receive opaque identifiers via
/// [PaneWatcherInput] and emit deltas using [PaneBranchContext] + payload
/// metadata. Hosts translate those into domain objects (threads, commits, etc).
abstract class PaneDeltaWatcherContract<TPayload> {
  PaneKey get paneKey;

  /// Subscribes to underlying data sources and emits raw delta events.
  Stream<PaneDeltaEvent> watch(PaneWatcherInput input);

  /// Resolves a delta event into a payload suitable for hydrator ingestion.
  Future<PaneHydrationDelta<TPayload>> resolve(PaneDeltaEvent event);
}
