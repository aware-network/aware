import 'package:flutter_test/flutter_test.dart';

import 'package:aware_widgets/src/kinematics/kinematic_glass.dart';

void main() {
  test('KinematicValues.opacity does not include breathing', () {
    const values = KinematicValues(
      breathOpacity: -0.25,
      breathBlur: 0.0,
      settleScale: 1.0,
      settleOffset: 0.0,
      settleOpacity: 0.7,
      responseScale: 1.0,
      hoverT: 0.0,
      hoverScale: 1.0,
      hoverLift: 0.0,
      floatOffset: Offset.zero,
      isPressed: false,
      isHovered: false,
    );

    expect(values.opacity, 0.7);
  });
}
