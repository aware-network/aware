import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('PaneValueMemo caches value for same key', () {
    final memo = PaneValueMemo<int>();
    var calls = 0;

    final first = memo.getOrCompute(
      key: 'a',
      compute: () {
        calls += 1;
        return 1;
      },
    );
    expect(first, 1);
    expect(calls, 1);

    final second = memo.getOrCompute(
      key: 'a',
      compute: () {
        calls += 1;
        return 2;
      },
    );
    expect(second, 1);
    expect(calls, 1);
  });

  test('PaneValueMemo recomputes when key changes', () {
    final memo = PaneValueMemo<int>();
    var calls = 0;

    expect(
      memo.getOrCompute(
        key: 'a',
        compute: () {
          calls += 1;
          return 1;
        },
      ),
      1,
    );
    expect(calls, 1);

    expect(
      memo.getOrCompute(
        key: 'b',
        compute: () {
          calls += 1;
          return 2;
        },
      ),
      2,
    );
    expect(calls, 2);
  });

  test('PaneValueMemo caches errors by default', () {
    final memo = PaneValueMemo<int>();
    var calls = 0;

    expect(
      () => memo.getOrCompute(
        key: 'a',
        compute: () {
          calls += 1;
          throw StateError('boom');
        },
      ),
      throwsA(isA<StateError>()),
    );
    expect(calls, 1);

    // Same key => no recompute, error rethrown.
    expect(
      () => memo.getOrCompute(
        key: 'a',
        compute: () {
          calls += 1;
          return 1;
        },
      ),
      throwsA(isA<StateError>()),
    );
    expect(calls, 1);

    // New key => recompute allowed.
    expect(
      memo.getOrCompute(
        key: 'b',
        compute: () {
          calls += 1;
          return 7;
        },
      ),
      7,
    );
    expect(calls, 2);
  });

  test('PaneValueMemo does not cache errors when cacheError=false', () {
    final memo = PaneValueMemo<int>();
    var calls = 0;

    expect(
      () => memo.getOrCompute(
        key: 'a',
        cacheError: false,
        compute: () {
          calls += 1;
          throw StateError('boom');
        },
      ),
      throwsA(isA<StateError>()),
    );
    expect(calls, 1);

    expect(
      memo.getOrCompute(
        key: 'a',
        cacheError: false,
        compute: () {
          calls += 1;
          return 42;
        },
      ),
      42,
    );
    expect(calls, 2);
  });
}
