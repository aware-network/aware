import 'package:flutter/material.dart';

class WindowDivider extends StatelessWidget {
  const WindowDivider({
    super.key,
    required this.isVertical,
    required this.onDrag,
    required this.borderColor,
  });

  final bool isVertical;
  final void Function(double delta) onDrag;
  final Color borderColor;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onHorizontalDragUpdate: isVertical
          ? (details) => onDrag(details.delta.dx)
          : null,
      onVerticalDragUpdate: !isVertical
          ? (details) => onDrag(details.delta.dy)
          : null,
      child: MouseRegion(
        cursor: isVertical
            ? SystemMouseCursors.resizeColumn
            : SystemMouseCursors.resizeRow,
        child: Container(
          width: isVertical ? 4 : double.infinity,
          height: isVertical ? double.infinity : 4,
          color: borderColor.withValues(alpha: 0.3),
          child: Center(
            child: Container(
              width: isVertical ? 4 : 30,
              height: isVertical ? 30 : 4,
              decoration: BoxDecoration(
                color: borderColor.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
