import 'package:uuid/uuid.dart';

class CapabilityResolver {
  CapabilityResolver({required Object? capabilities})
      : _capabilities = _asJsonMapOrNull(capabilities);

  final Map<String, dynamic>? _capabilities;

  Iterable<Map<String, dynamic>> get objects =>
      _jsonObjectList(_capabilities?['objects']);

  Iterable<Map<String, dynamic>> get functions =>
      _jsonObjectList(_capabilities?['functions']);

  Iterable<Map<String, dynamic>> get roles =>
      _jsonObjectList(_capabilities?['roles']);

  UuidValue? resolveFunctionId({
    required String objectName,
    required String functionName,
  }) {
    final function = resolveFunction(
      objectName: objectName,
      functionName: functionName,
    );
    final rawId = function?['id'];
    if (rawId == null) return null;
    return UuidValue.fromString(rawId.toString());
  }

  Map<String, dynamic>? resolveFunction({
    required String objectName,
    required String functionName,
  }) {
    final objectKey = _normalizeToken(objectName);
    final functionKey = _normalizeToken(functionName);
    if (objectKey.isEmpty || functionKey.isEmpty) return null;

    for (final object in objects) {
      if (_normalizeToken(object['name']?.toString() ?? '') != objectKey) {
        continue;
      }
      for (final function in _jsonObjectList(object['functions'])) {
        if (_normalizeToken(function['name']?.toString() ?? '') ==
            functionKey) {
          return function;
        }
      }
    }

    for (final function in functions) {
      if (_normalizeToken(function['name']?.toString() ?? '') == functionKey) {
        return function;
      }
    }

    return null;
  }

  static String _normalizeToken(String token) {
    var value = token.trim().toLowerCase();
    value = value.replaceAll(RegExp(r'[^a-z0-9]'), '');
    return value;
  }
}

Map<String, dynamic>? _asJsonMapOrNull(Object? value) {
  if (value == null) return null;
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  throw ArgumentError(
    'Capabilities payload must be a JSON object, got ${value.runtimeType}.',
  );
}

Iterable<Map<String, dynamic>> _jsonObjectList(Object? value) sync* {
  if (value == null) return;
  if (value is! Iterable) return;
  for (final entry in value) {
    if (entry is Map<String, dynamic>) {
      yield entry;
    } else if (entry is Map) {
      yield Map<String, dynamic>.from(entry);
    }
  }
}
