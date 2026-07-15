import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

class WindowCommandIntent {
  const WindowCommandIntent({required this.commandId, this.payload});

  final String commandId;
  final Map<String, dynamic>? payload;
}

class WindowCommandRouter {
  WindowCommandRouter(this.windowId);

  final String windowId;
  final StreamController<WindowCommandIntent> _controller =
      StreamController<WindowCommandIntent>.broadcast();

  Stream<WindowCommandIntent> get stream => _controller.stream;

  void emit(WindowCommandIntent intent) {
    if (_controller.isClosed) {
      return;
    }
    _controller.add(intent);
  }

  void dispose() {
    _controller.close();
  }
}

final windowCommandRouterProvider =
    Provider.family<WindowCommandRouter, String>((ref, windowId) {
      final router = WindowCommandRouter(windowId);
      ref.onDispose(router.dispose);
      return router;
    });
