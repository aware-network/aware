import 'package:flutter_test/flutter_test.dart';

import 'package:aware_widgets/src/tokens/aware_motion.dart';

void main() {
  test('AwareMotion.dampingRatioForOvershoot is monotonic', () {
    expect(AwareMotion.dampingRatioForOvershoot(0), 1.0);

    final lowOvershoot = AwareMotion.dampingRatioForOvershoot(0.05);
    final highOvershoot = AwareMotion.dampingRatioForOvershoot(0.35);

    expect(lowOvershoot, greaterThan(highOvershoot));
    expect(lowOvershoot, greaterThan(0));
    expect(highOvershoot, greaterThan(0));
  });

  test('GlassSprings.release clamps damping ratio for calmness', () {
    final spring = GlassSprings.release(
      pressScale: 0.985,
      releaseOvershoot: 1.004,
    );

    final ratio = AwareMotion.dampingRatio(
      mass: spring.mass,
      stiffness: spring.stiffness,
      damping: spring.damping,
    );

    expect(ratio, inInclusiveRange(0.72, 1.25));
  });
}
