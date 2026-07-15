import 'package:flutter_test/flutter_test.dart';

import 'package:aware_widgets/src/layout/glass_layout_simulation.dart';
import 'package:aware_widgets/src/tokens/aware_motion.dart';

void main() {
  test('GlassLayoutSimulation syncTargets grows and shrinks safely', () {
    final sim = GlassLayoutSimulation(
      spring: AwareMotion.spring(stiffness: 200, dampingRatio: 0.9),
    );

    sim.syncTargets(const [0, 100, 200]);
    expect(sim.count, 3);
    expect(sim.positionFor(0), 0);
    expect(sim.positionFor(1), 100);
    expect(sim.positionFor(2), 200);

    sim.syncTargets(const []);
    expect(sim.count, 0);

    sim.syncTargets(const [0, 50]);
    expect(sim.count, 2);
    expect(sim.positionFor(0), 0);
    expect(sim.positionFor(1), 50);
  });

  test(
    'GlassLayoutSimulation resolves overlap immediately (no collision frame)',
    () {
      final sim = GlassLayoutSimulation(
        spring: AwareMotion.spring(stiffness: 180, dampingRatio: 0.9),
      );

      sim.syncTargets(const [0, 100]);
      expect(sim.positionFor(1), 100);

      // Simulate an expansion above: the required delta jumps up.
      // The constraint should apply immediately so the next paint never overlaps.
      sim.syncTargets(const [0, 220]);
      expect(sim.positionFor(1), 220);
      expect(sim.pressureFor(0), greaterThan(0));
      expect(sim.pressureFor(1), greaterThan(0));
    },
  );
}
