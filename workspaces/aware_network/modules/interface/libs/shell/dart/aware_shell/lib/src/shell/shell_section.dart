import 'package:aware_windows/aware_windows.dart';

class InterfaceShellSection {
  const InterfaceShellSection({
    required this.sectionKey,
    required this.region,
    required this.order,
    this.title,
    this.flex = 1.0,
    this.isVisible = true,
    this.transitionSectionId,
    this.weightMicros,
    this.isCollapsed = false,
  });

  final String sectionKey;
  final WindowFullscreenSectionRegion region;
  final int order;
  final String? title;
  final double flex;
  final bool isVisible;
  final String? transitionSectionId;
  final int? weightMicros;
  final bool isCollapsed;
}
