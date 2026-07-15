/// Identifier used by the pane registry.
///
/// We intentionally keep this as an opaque string so host applications can
/// define their own taxonomy (enums, value objects, etc.) and pass the string
/// representation into the shared runtime.
typedef PaneKey = String;

/// Helper for consistent pane key creation.
class PaneKeys {
  PaneKeys._();

  /// Normalises an arbitrary identifier into a pane key.
  static PaneKey normalize(String value) => value.trim();
}
