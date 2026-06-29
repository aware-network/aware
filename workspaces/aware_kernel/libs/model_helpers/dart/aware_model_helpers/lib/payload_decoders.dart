import 'dart:convert';
import 'dart:typed_data';

import 'package:uuid/uuid.dart';

import 'converters.dart';

Map<String, dynamic> decodeMap(Object? value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  throw StateError(
    'Expected Map<String, dynamic> but got ${value.runtimeType}',
  );
}

List<T> decodeList<T>(Object? value, T Function(Object? item) decode) {
  if (value is List) {
    return value.map((item) => decode(item)).toList();
  }
  throw StateError('Expected List but got ${value.runtimeType}');
}

List<T>? decodeListOrNull<T>(Object? value, T Function(Object? item) decode) {
  if (value == null) return null;
  return decodeList(value, decode);
}

Set<T> decodeSet<T>(Object? value, T Function(Object? item) decode) {
  return decodeList(value, decode).toSet();
}

Set<T>? decodeSetOrNull<T>(Object? value, T Function(Object? item) decode) {
  if (value == null) return null;
  return decodeSet(value, decode);
}

String decodeString(Object? value) {
  if (value == null) {
    throw StateError('Expected String but got null');
  }
  return value.toString();
}

String? decodeStringOrNull(Object? value) {
  return value?.toString();
}

int? decodeIntOrNull(Object? value) {
  if (value == null) return null;
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value.toString());
}

int decodeInt(Object? value) {
  final decoded = decodeIntOrNull(value);
  if (decoded == null) {
    throw StateError('Expected int but got ${value.runtimeType}');
  }
  return decoded;
}

double? decodeDoubleOrNull(Object? value) {
  if (value == null) return null;
  if (value is double) return value;
  if (value is num) return value.toDouble();
  return double.tryParse(value.toString());
}

double decodeDouble(Object? value) {
  final decoded = decodeDoubleOrNull(value);
  if (decoded == null) {
    throw StateError('Expected double but got ${value.runtimeType}');
  }
  return decoded;
}

bool? decodeBoolOrNull(Object? value) {
  if (value == null) return null;
  if (value is bool) return value;
  final normalized = value.toString().toLowerCase();
  if (normalized == 'true') return true;
  if (normalized == 'false') return false;
  return null;
}

bool decodeBool(Object? value) {
  final decoded = decodeBoolOrNull(value);
  if (decoded == null) {
    throw StateError('Expected bool but got ${value.runtimeType}');
  }
  return decoded;
}

DateTime? decodeDateTimeOrNull(Object? value) {
  if (value == null) return null;
  if (value is DateTime) return value;
  return DateTime.tryParse(value.toString());
}

DateTime decodeDateTime(Object? value) {
  final decoded = decodeDateTimeOrNull(value);
  if (decoded == null) {
    throw StateError('Expected DateTime but got ${value.runtimeType}');
  }
  return decoded;
}

Map<String, dynamic>? decodeJsonObjectOrNull(Object? value) {
  if (value == null) return null;
  return decodeMap(value);
}

Map<String, dynamic> decodeJsonObject(Object? value) {
  final decoded = decodeJsonObjectOrNull(value);
  if (decoded == null) {
    throw StateError('Expected Map<String, dynamic> but got null');
  }
  return decoded;
}

UuidValue? decodeUuidValueOrNull(Object? value) {
  if (value == null) return null;
  if (value is UuidValue) return value;
  return UuidValue.fromString(value.toString());
}

UuidValue decodeUuidValue(Object? value) {
  final decoded = decodeUuidValueOrNull(value);
  if (decoded == null) {
    throw StateError('Expected UuidValue but got null');
  }
  return decoded;
}

Uint8List? decodeBytesOrNull(Object? value) {
  if (value == null) return null;
  if (value is Uint8List) return value;
  if (value is String) return const Uint8ListConverter().fromJson(value);
  if (value is List<int>) return Uint8List.fromList(value);
  if (value is List) {
    return Uint8List.fromList(value.map((e) => decodeInt(e)).toList());
  }
  return null;
}

Uint8List decodeBytes(Object? value) {
  final decoded = decodeBytesOrNull(value);
  if (decoded == null) {
    throw StateError('Expected Uint8List but got ${value.runtimeType}');
  }
  return decoded;
}

dynamic decodeJsonValue(String json) => jsonDecode(json);
