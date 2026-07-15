# aware_messaging

Reusable command and event messaging primitives shared across Aware Flutter applications.

## Goals
- Provide framework-agnostic command/event buses with middleware hooks.
- Enable packages like `aware_windows` and `aware_pane` to share messaging behavior.
- Offer testing utilities and optional adapters without tying to any specific DI solution.

## Getting Started
```dart
import 'package:aware_messaging/aware_messaging.dart';

final commandBus = CommandBus();
commandBus.register<MyCommand, String>((cmd) async => CommandSuccess('ok'));

final eventBus = EventBus();
eventBus.subscribe<MyEvent>((event) async {});
```

See `lib/src/testing/` for in-memory test helpers and `lib/src/adapters/` for optional Riverpod bindings.

