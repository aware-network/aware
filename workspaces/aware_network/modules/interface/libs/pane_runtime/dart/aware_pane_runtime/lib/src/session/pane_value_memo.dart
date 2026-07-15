import 'package:flutter/widgets.dart';

import 'pane_controller_registry.dart';
import 'pane_session_registry.dart';

/// A simple "compute once per key" memo for pane session state.
///
/// Intended for expensive derived state (for example: OIG lane materialization)
/// that should recompute only when the underlying lane head changes.
class PaneValueMemo<T> {
  PaneValueMemo({this.debugLabel});

  final String? debugLabel;

  String? _key;
  bool _hasValue = false;
  T? _value;
  Object? _error;
  StackTrace? _errorStackTrace;
  int _computeCount = 0;

  String? get key => _key;
  bool get hasValue => _hasValue;
  bool get hasError => _error != null;
  int get computeCount => _computeCount;

  T? get value => _hasValue ? _value : null;
  Object? get error => _error;
  StackTrace? get errorStackTrace => _errorStackTrace;

  void clear() {
    _key = null;
    _hasValue = false;
    _value = null;
    _error = null;
    _errorStackTrace = null;
  }

  T getOrCompute({
    required String key,
    required T Function() compute,
    bool cacheError = true,
  }) {
    if (_key == key) {
      if (_hasValue) {
        return _value as T;
      }
      if (cacheError && _error != null) {
        Error.throwWithStackTrace(
          _error!,
          _errorStackTrace ?? StackTrace.current,
        );
      }
    } else {
      _key = key;
      _hasValue = false;
      _value = null;
      _error = null;
      _errorStackTrace = null;
    }

    try {
      final next = compute();
      _computeCount += 1;
      _value = next;
      _hasValue = true;
      _error = null;
      _errorStackTrace = null;
      return next;
    } catch (e, st) {
      _hasValue = false;
      _value = null;
      if (cacheError) {
        _error = e;
        _errorStackTrace = st;
      } else {
        _error = null;
        _errorStackTrace = null;
      }
      Error.throwWithStackTrace(e, st);
    }
  }
}

class PaneValueMemoEntry<T> extends PaneControllerEntry<PaneValueMemo<T>> {
  const PaneValueMemoEntry({this.debugLabel});

  final String? debugLabel;

  @override
  PaneValueMemo<T> create() => PaneValueMemo<T>(debugLabel: debugLabel);

  @override
  void dispose(PaneValueMemo<T> controller) {
    // No-op: memo has no native resources.
  }
}

/// Convenience: session-scoped memoization for expensive derived state.
///
/// If no pane session/controller scope is present, [compute] is executed
/// directly without memoization.
T paneSessionMemoize<T>({
  required BuildContext context,
  required String controllerKey,
  required String key,
  required T Function() compute,
  String? debugLabel,
  bool cacheError = true,
}) {
  final sessionContext = PaneSessionScope.maybeContext(context);
  final registry = PaneControllerScope.maybeOf(context);
  if (sessionContext == null || registry == null) {
    return compute();
  }

  final memo = registry.obtain(
    sessionContext.windowSessionId,
    sessionContext.paneInstanceId,
    controllerKey,
    PaneValueMemoEntry<T>(debugLabel: debugLabel ?? controllerKey),
  );

  return memo.getOrCompute(key: key, compute: compute, cacheError: cacheError);
}
