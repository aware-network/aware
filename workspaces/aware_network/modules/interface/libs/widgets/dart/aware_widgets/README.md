# aware_widgets

Opinionated glass UI primitives, motion, and design tokens for Flutter.

This package gives you a cohesive “glass” feel built from a few parts:

- Glass materials: blur + tint + specular highlights
- Kinematics: settling, hover/parallax, press feedback, and shared ambient shear
- Layout: a physics-aware Column/Row replacement for animated reflow
- Tokens: colors, shadows, gradients, and spring presets

The API is intentionally compositional: most widgets are small building blocks you can mix into your own UI.

## Install

Add the package as a dependency (path or git are the most common options while developing):

```yaml
dependencies:
  aware_widgets:
    path: ../aware_widgets
```

```yaml
dependencies:
  aware_widgets:
    git:
      url: <your-repo-url>
      path: <repo-subdir-containing-aware_widgets>
```

Then run `flutter pub get`.

Minimum SDKs (from `pubspec.yaml`):

- Dart: `>=3.4.4 <4.0.0`
- Flutter: `>=3.0.0`

## Quick Start (Copy/Paste)

This example wires up an app-wide `GlassFieldController` and drives it from the mouse to demonstrate coherent kinematics.

```dart
import 'package:aware_widgets/aware_widgets.dart';
import 'package:flutter/material.dart';

void main() => runApp(const DemoApp());

class DemoApp extends StatefulWidget {
  const DemoApp({super.key});

  @override
  State<DemoApp> createState() => _DemoAppState();
}

class _DemoAppState extends State<DemoApp> {
  final _glassField = GlassFieldController();

  @override
  void dispose() {
    _glassField.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GlassFieldScope(
      controller: _glassField,
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: ThemeData.dark(useMaterial3: true),
        home: Scaffold(
          body: LayoutBuilder(
            builder: (context, constraints) {
              final size = constraints.biggest;

              return MouseRegion(
                onHover: (event) {
                  if (size.width <= 0 || size.height <= 0) return;

                  final nx = ((event.localPosition.dx / size.width) - 0.5) * 2; // -1..1
                  final ny = ((event.localPosition.dy / size.height) - 0.5) * 2; // -1..1
                  _glassField.shear = Offset(nx, ny);
                },
                onExit: (_) => _glassField.shear = Offset.zero,
                child: Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Color(0xFF0B1020), Color(0xFF000000)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                  alignment: Alignment.center,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 520),
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: GlassLayout(
                        spacing: 16,
                        children: [
                          AwareGlassPane(
                            borderRadius: BorderRadius.circular(24),
                            child: Padding(
                              padding: const EdgeInsets.all(24),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'aware_widgets',
                                    style: Theme.of(context).textTheme.headlineSmall,
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Glass materials + coherent motion + springy layout.',
                                    style: Theme.of(context).textTheme.bodyMedium,
                                  ),
                                  const SizedBox(height: 20),
                                  Wrap(
                                    spacing: 12,
                                    runSpacing: 12,
                                    children: [
                                      GlassActionButton(
                                        label: 'Action',
                                        icon: Icons.auto_awesome,
                                        onPressed: () {},
                                      ),
                                      GlassActionButton(
                                        label: 'Loading',
                                        loading: true,
                                        onPressed: () {},
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                          AwareGlassCard(
                            onTap: () {},
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Tap me',
                                  style: Theme.of(context).textTheme.titleMedium,
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  'This uses kinematic press feedback.',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
```

## Core Concepts

### Glass materials

Use `AwareGlassMaterial` when you want the base effect (blur + tint + edge highlights). Use `AwareGlassCard` and `AwareGlassPane` as higher-level, pre-styled surfaces.

```dart
AwareGlassMaterial(
  child: Padding(
    padding: const EdgeInsets.all(16),
    child: Text('Hello, glass'),
  ),
)
```

Variants:

- `GlassMaterialVariant` (smoked/frost/deepSpace/inset) for presets
- `GlassSurface` (panel/inset/chip/soft) for “role”-based tuning

### Kinematics (motion that stays coherent)

`KinematicGlass` is a wrapper you can apply to any widget to add:

- Settle-on-appear (spring landing)
- Hover lift + pointer parallax (desktop/web)
- Press feedback (touch/click)

Most “glass” widgets in this package already use `KinematicGlass` internally, but you can wrap your own surfaces too.

`GlassFieldScope` provides an app-wide `GlassFieldController` (an `InheritedNotifier`) that glass widgets can read to apply a consistent ambient shear. The controller clamps to `-1..1` and ignores tiny jitter.

### Physics-aware layout (animated reflow)

`GlassLayout` is a drop-in replacement for `Column` / `Row` when you want layout changes to feel physical:

- When one child expands/collapses, siblings spring to their new positions instead of “jumping”.
- Use `GlassLayoutPhysics` presets (`snappy`, `smooth`, `liquid`, `bouncy`, `heavy`) to tune the feel.

## Design Invariants (Rationale)

These are the constraints that keep a glass UI readable, stable, and performant:

- Keep blur anchored: avoid translating/scaling a `BackdropFilter` every frame. Prefer animating cheap overlays (highlights, shadows) on top of a stable blur region.
- Use a shared motion field: route ambient “tilt/shear” through one `GlassFieldController` so multiple surfaces don’t drift out of sync.
- Avoid teleporting layout: animate reflow (via `GlassLayout`) so a size change in one widget doesn’t create a discontinuity for everything around it.
- Avoid parallax feedback loops: if you derive motion from pointer position, compute it in an untransformed coordinate space (don’t measure pointer deltas on a widget that you’re actively translating).
- Respect reduced motion: prefer presets that settle quickly, and avoid always-on animations when `MediaQuery.disableAnimations` is true.

## API Overview

Materials:

- `AwareGlassMaterial`
- `AwareGlassCard` (+ `GlassCardHeader`, `GlassInset`, `GlassExpandable`, `GlassToggleControl`, `GlassActionButton`, `GlassPrimaryAction`)
- `AwareGlassPane`

Motion:

- `KinematicGlass`
- `GlassKinematicPreset`, `GlassBreathing`, `GlassSettling`, `GlassResponse`, `GlassHover`, `GlassFloating`
- `GlassFieldController`, `GlassFieldScope`

Layout:

- `GlassLayout`
- `GlassLayoutPhysics`

Tokens:

- `AwareColors`, `AwareShadows`, `AwareGradients`
- `AwareMotion`, `GlassSprings`

Diagnostics:

- `GlassTickerDiagnostics` (best-effort runtime counters for common tickers)

## Performance Notes

- Blur is expensive. Prefer using glass surfaces for panels/cards, not for every tiny list row.
- Keep large blurred subtrees stable (avoid rebuilding them on high-frequency signals).
- If you need “alive” motion, prefer subtle hover/parallax over continuous breathing on large surfaces.

## Testing

From this package directory:

```bash
flutter test
```
