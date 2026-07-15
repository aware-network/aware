import '../../pane_kind.dart';
import 'pane_registry.dart';

String _normalizeToken(String token) => token.trim().toLowerCase();

/// Resolve which pane kind should be mounted for a workspace selection.
///
/// This lives in `aware_pane_runtime` so the Interface app can remain a thin
/// shell: it supplies `(opgName)` and/or `(opgIdentityKey, viewKey)`, while the
/// mapping logic stays canonical and reusable.
PaneKey? resolvePaneKind({
  required Iterable<PaneKey> registeredPanes,
  required PaneOpgBinding? Function(PaneKey kind) bindingFor,
  Iterable<PaneOpgViewBinding> Function(PaneKey kind)? viewBindingsFor,
  String? opgName,
  String? opgIdentityKey,
  String? viewKey,
}) {
  if (viewBindingsFor != null &&
      opgIdentityKey != null &&
      viewKey != null &&
      _normalizeToken(opgIdentityKey).isNotEmpty &&
      _normalizeToken(viewKey).isNotEmpty) {
    final opgIdentityNeedle = _normalizeToken(opgIdentityKey);
    final viewNeedle = _normalizeToken(viewKey);
    for (final kind in registeredPanes) {
      for (final binding in viewBindingsFor(kind)) {
        if (_normalizeToken(binding.opgIdentityKey) == opgIdentityNeedle &&
            _normalizeToken(binding.viewKey) == viewNeedle) {
          return kind;
        }
      }
    }
  }

  final normalizedOpgName = opgName == null ? '' : _normalizeToken(opgName);
  if (normalizedOpgName.isEmpty) return null;

  for (final kind in registeredPanes) {
    final binding = bindingFor(kind);
    if (binding == null) continue;
    if (_normalizeToken(binding.opgName) == normalizedOpgName) {
      return kind;
    }
  }

  return null;
}
