import 'package:aware_model_helpers/aware_decimal.dart';
import 'package:aware_model_helpers/payload_decoders.dart' as payload_decoders;
import 'package:test/test.dart';

void main() {
  test('canonical text converges equivalent exact values', () {
    expect(AwareDecimal.parse('1').toJson(), '1');
    expect(AwareDecimal.parse('1.0').toJson(), '1');
    expect(AwareDecimal.parse('1.2300').toJson(), '1.23');
    expect(AwareDecimal.parse('-0.000').toJson(), '0');
  });

  test('arithmetic stays exact', () {
    final result = AwareDecimal.parse('0.1') + AwareDecimal.parse('0.2');
    expect(result.toJson(), '0.3');
  });

  test('JSON and payload decoding reject numeric values', () {
    expect(() => AwareDecimal.fromJson(1.25), throwsFormatException);
    expect(() => payload_decoders.decodeAwareDecimal(1.25), throwsStateError);
  });

  test('JSON and payload decoding accept exact text', () {
    expect(AwareDecimal.fromJson('12.3400').toJson(), '12.34');
    expect(
      payload_decoders.decodeAwareDecimal('12.3400').toJson(),
      '12.34',
    );
  });
}
