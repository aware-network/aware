import 'package:flutter_test/flutter_test.dart';

import 'package:aware_widgets/src/kinematics/glass_kinematics.dart';

void main() {
  test('GlassFloating followTouch defaults to false', () {
    const config = GlassFloating();
    expect(config.followTouch, isFalse);
    expect(GlassFloating.subtle.followTouch, isFalse);
    expect(GlassFloating.interactive.followTouch, isFalse);
    expect(GlassFloating.none.followTouch, isFalse);
  });
}
