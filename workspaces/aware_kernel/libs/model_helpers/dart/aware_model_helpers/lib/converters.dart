import 'dart:convert';
import 'dart:typed_data';

import 'package:json_annotation/json_annotation.dart';
import 'package:uuid/uuid.dart';
import 'package:intl/intl.dart';

/// JSON type converter utilities for serialization and deserialization

/// UUID Type converter for Freezed models
///
/// This converter handles serializing UuidValue objects to strings
/// and deserializing strings to UuidValue objects.
class UuidValueConverter implements JsonConverter<UuidValue, String> {
  const UuidValueConverter();

  @override
  UuidValue fromJson(String json) => UuidValue.fromString(json);

  @override
  String toJson(UuidValue object) => object.uuid;
}

/// Nullable UUID converter that handles null values
class NullableUuidValueConverter implements JsonConverter<UuidValue?, String?> {
  const NullableUuidValueConverter();

  @override
  UuidValue? fromJson(String? json) {
    if (json == null) return null;
    return UuidValue.fromString(json);
  }

  @override
  String? toJson(UuidValue? object) {
    return object?.toString();
  }
}

/// DateTime converter for ISO 8601 format
class DateTimeConverter implements JsonConverter<DateTime, String> {
  const DateTimeConverter();

  @override
  DateTime fromJson(String json) {
    return DateTime.parse(json);
  }

  @override
  String toJson(DateTime object) {
    return object.toIso8601String();
  }
}

/// Nullable DateTime converter
class NullableDateTimeConverter implements JsonConverter<DateTime?, String?> {
  const NullableDateTimeConverter();

  @override
  DateTime? fromJson(String? json) {
    if (json == null) return null;
    return DateTime.parse(json);
  }

  @override
  String? toJson(DateTime? object) {
    return object?.toIso8601String();
  }
}

/// Date converter using a specific format (yyyy-MM-dd)
class DateConverter implements JsonConverter<DateTime, String> {
  static final DateFormat _formatter = DateFormat('yyyy-MM-dd');
  const DateConverter();

  @override
  DateTime fromJson(String json) {
    return _formatter.parse(json);
  }

  @override
  String toJson(DateTime object) {
    return _formatter.format(object);
  }
}

/// Nullable Date converter
class NullableDateConverter implements JsonConverter<DateTime?, String?> {
  static final DateFormat _formatter = DateFormat('yyyy-MM-dd');
  const NullableDateConverter();

  @override
  DateTime? fromJson(String? json) {
    if (json == null) return null;
    return _formatter.parse(json);
  }

  @override
  String? toJson(DateTime? object) {
    if (object == null) return null;
    return _formatter.format(object);
  }
}

/// Map to JSON converter that handles complex objects
class MapJsonConverter<K, V>
    implements JsonConverter<Map<K, V>, Map<String, dynamic>> {
  final K Function(String) keyFromJson;
  final String Function(K) keyToJson;
  final V Function(dynamic) valueFromJson;
  final dynamic Function(V) valueToJson;

  const MapJsonConverter({
    required this.keyFromJson,
    required this.keyToJson,
    required this.valueFromJson,
    required this.valueToJson,
  });

  @override
  Map<K, V> fromJson(Map<String, dynamic> json) {
    return json.map(
      (key, value) => MapEntry(keyFromJson(key), valueFromJson(value)),
    );
  }

  @override
  Map<String, dynamic> toJson(Map<K, V> map) {
    return map.map(
      (key, value) => MapEntry(keyToJson(key), valueToJson(value)),
    );
  }
}

/// List of UuidValues converter
class UuidValueListConverter
    implements JsonConverter<List<UuidValue>, List<dynamic>> {
  const UuidValueListConverter();

  @override
  List<UuidValue> fromJson(List<dynamic> json) {
    return json.map((e) => UuidValue.fromString(e as String)).toList();
  }

  @override
  List<dynamic> toJson(List<UuidValue> object) {
    return object.map((e) => e.toString()).toList();
  }
}

class Uint8ListConverter implements JsonConverter<Uint8List, String> {
  const Uint8ListConverter();

  @override
  Uint8List fromJson(String json) {
    return base64Decode(json);
  }

  @override
  String toJson(Uint8List object) {
    return base64Encode(object);
  }
}

class MapConverter<T>
    implements JsonConverter<Map<String, T>, Map<String, dynamic>> {
  final T Function(Map<String, dynamic>) fromJsonT;

  const MapConverter(this.fromJsonT);

  @override
  Map<String, T> fromJson(Map<String, dynamic> json) =>
      json.map((k, v) => MapEntry(k, fromJsonT(v as Map<String, dynamic>)));

  @override
  Map<String, dynamic> toJson(Map<String, T> object) =>
      object.map((k, v) => MapEntry(k, (v as dynamic).toJson()));
}
