library aware_node_session_status_pane;

import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:aware_widgets/aware_widgets.dart';
import 'package:flutter/material.dart';

const String _panePackageName = 'aware-node-session-status-pane';
const PaneKey _paneKind = 'node_session_status';

void registerPanePackage(PanePackageRegistry registry) {
  registry.registerPanePackage(
    panePackageId: stablePanePackageId(name: _panePackageName),
    panePackageName: _panePackageName,
    paneKind: _paneKind,
    capabilities: const runtime.PaneCapabilities(
      provides: {'node.session_status'},
      emits: {'node.session_status.event'},
      framePolicy: runtime.PaneFramePolicy.embedded,
    ),
    displayInfo: const runtime.PaneDisplayInfo(
      paneKey: _paneKind,
      title: 'Node Session Status',
      description: 'Your link to the Aware Network — connection liveness.',
    ),
    factory: (paneContext) => NodeSessionStatusPane(paneContext: paneContext),
  );
}

/// Connection-liveness pane: brand-pink role surface that visualizes the
/// visitor's link to the Aware Network with a single signal arc and the
/// minimum status fields.
class NodeSessionStatusPane extends StatelessWidget {
  const NodeSessionStatusPane({super.key, required this.paneContext});

  final PaneContext paneContext;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Material(
      color: Colors.transparent,
      child: Padding(
        padding: const EdgeInsets.all(4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            const _RoleBadge(
              index: '03',
              label: 'CONNECTION',
              color: AwareColors.connectionRole,
            ),
            const SizedBox(height: 10),
            Text(
              'Your link to the network.',
              style: theme.textTheme.titleMedium?.copyWith(
                color: Colors.white.withValues(alpha: 0.94),
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.03),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AwareColors.connectionRole.withValues(alpha: 0.22),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(
                    height: 64,
                    child: _SignalArc(),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: const [
                      _StatusPill(label: 'LIVE'),
                      _PlaceholderText(text: 'Aware Interface Host'),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SignalArc extends StatefulWidget {
  const _SignalArc();

  @override
  State<_SignalArc> createState() => _SignalArcState();
}

class _SignalArcState extends State<_SignalArc>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 8),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return CustomPaint(
          painter: _SignalArcPainter(progress: _controller.value),
        );
      },
    );
  }
}

class _SignalArcPainter extends CustomPainter {
  _SignalArcPainter({required this.progress});

  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final start = Offset(8, size.height * 0.78);
    final control = Offset(size.width / 2, -size.height * 0.18);
    final end = Offset(size.width - 8, size.height * 0.78);

    final path = Path()
      ..moveTo(start.dx, start.dy)
      ..quadraticBezierTo(control.dx, control.dy, end.dx, end.dy);

    final guide = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0
      ..color = AwareColors.connectionRole.withValues(alpha: 0.18);
    canvas.drawPath(path, guide);

    final t = progress;
    final position = _quadratic(start, control, end, t);

    final glow = Paint()
      ..style = PaintingStyle.fill
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12)
      ..color = AwareColors.connectionRole.withValues(alpha: 0.42);
    canvas.drawCircle(position, 9, glow);

    final head = Paint()
      ..style = PaintingStyle.fill
      ..color = AwareColors.connectionRole;
    canvas.drawCircle(position, 3.4, head);

    final trail = Paint()..style = PaintingStyle.fill;
    for (var step = 1; step <= 5; step++) {
      final tt = t - step * 0.018;
      if (tt <= 0 || tt >= 1) continue;
      final p = _quadratic(start, control, end, tt);
      final alpha = (0.55 - step * 0.10).clamp(0.05, 0.55);
      trail.color = AwareColors.connectionRole.withValues(alpha: alpha);
      canvas.drawCircle(p, 2.3 - step * 0.3, trail);
    }
  }

  Offset _quadratic(Offset a, Offset b, Offset c, double t) {
    final u = 1.0 - t;
    return Offset(
      u * u * a.dx + 2 * u * t * b.dx + t * t * c.dx,
      u * u * a.dy + 2 * u * t * b.dy + t * t * c.dy,
    );
  }

  @override
  bool shouldRepaint(covariant _SignalArcPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AwareColors.connectionRole.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: AwareColors.connectionRole.withValues(alpha: 0.62),
        ),
      ),
      child: Text(
        label,
        style: theme.textTheme.labelSmall?.copyWith(
          color: Colors.white.withValues(alpha: 0.94),
          letterSpacing: 0.8,
        ),
      ),
    );
  }
}

class _PlaceholderText extends StatelessWidget {
  const _PlaceholderText({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Text(
      text,
      style: theme.textTheme.bodySmall?.copyWith(
        color: Colors.white.withValues(alpha: 0.62),
      ),
    );
  }
}

class _RoleBadge extends StatelessWidget {
  const _RoleBadge({
    required this.index,
    required this.label,
    required this.color,
  });

  final String index;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 6,
          height: 6,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: color.withValues(alpha: 0.6),
                blurRadius: 6,
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '$index · $label',
          style: theme.textTheme.labelSmall?.copyWith(
            color: Colors.white.withValues(alpha: 0.7),
            letterSpacing: 1.4,
          ),
        ),
      ],
    );
  }
}
