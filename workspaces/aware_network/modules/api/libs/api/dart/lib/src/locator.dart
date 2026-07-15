import 'client.dart';

class AwareApiLocator {
  const AwareApiLocator._();

  static AwareApiClient? _instance;

  static void initialize(AwareApiClient client) {
    _instance = client;
  }

  static AwareApiClient of() {
    final client = _instance;
    if (client == null) {
      throw StateError(
        'AwareApiLocator has not been initialized. Ensure the app sets it '
        'during bootstrap before invoking generated functions.',
      );
    }
    return client;
  }
}
