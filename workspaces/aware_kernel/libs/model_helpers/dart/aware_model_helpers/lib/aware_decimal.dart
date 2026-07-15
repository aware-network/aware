import 'package:decimal/decimal.dart' as exact;
import 'package:json_annotation/json_annotation.dart';

final class AwareDecimal implements Comparable<AwareDecimal> {
  final exact.Decimal _value;

  const AwareDecimal._(this._value);

  factory AwareDecimal.parse(String source) {
    final text = source.trim();
    if (text.isEmpty) {
      throw const FormatException('Decimal text must not be empty');
    }
    return AwareDecimal._(exact.Decimal.parse(text));
  }

  factory AwareDecimal.fromInt(int value) =>
      AwareDecimal._(exact.Decimal.fromInt(value));

  factory AwareDecimal.fromJson(Object? value) {
    if (value is! String) {
      throw FormatException(
        'Decimal JSON input must be decimal text, got ${value.runtimeType}',
      );
    }
    return AwareDecimal.parse(value);
  }

  String toJson() => _value.toString();

  AwareDecimal operator +(AwareDecimal other) =>
      AwareDecimal._(_value + other._value);

  AwareDecimal operator -(AwareDecimal other) =>
      AwareDecimal._(_value - other._value);

  AwareDecimal operator *(AwareDecimal other) =>
      AwareDecimal._(_value * other._value);

  AwareDecimal operator -() => AwareDecimal._(-_value);

  @override
  int compareTo(AwareDecimal other) => _value.compareTo(other._value);

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AwareDecimal && _value == other._value);

  @override
  int get hashCode => _value.hashCode;

  @override
  String toString() => toJson();
}

class AwareDecimalConverter implements JsonConverter<AwareDecimal, String> {
  const AwareDecimalConverter();

  @override
  AwareDecimal fromJson(String json) => AwareDecimal.parse(json);

  @override
  String toJson(AwareDecimal object) => object.toJson();
}

class NullableAwareDecimalConverter
    implements JsonConverter<AwareDecimal?, String?> {
  const NullableAwareDecimalConverter();

  @override
  AwareDecimal? fromJson(String? json) =>
      json == null ? null : AwareDecimal.parse(json);

  @override
  String? toJson(AwareDecimal? object) => object?.toJson();
}

class AwareDecimalListConverter
    implements JsonConverter<List<AwareDecimal>, List<String>> {
  const AwareDecimalListConverter();

  @override
  List<AwareDecimal> fromJson(List<String> json) =>
      json.map(AwareDecimal.parse).toList();

  @override
  List<String> toJson(List<AwareDecimal> object) =>
      object.map((value) => value.toJson()).toList();
}

class NullableAwareDecimalListConverter
    implements JsonConverter<List<AwareDecimal>?, List<String>?> {
  const NullableAwareDecimalListConverter();

  @override
  List<AwareDecimal>? fromJson(List<String>? json) =>
      json?.map(AwareDecimal.parse).toList();

  @override
  List<String>? toJson(List<AwareDecimal>? object) =>
      object?.map((value) => value.toJson()).toList();
}
