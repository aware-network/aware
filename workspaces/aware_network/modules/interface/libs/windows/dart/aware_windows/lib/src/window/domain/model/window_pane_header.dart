import 'package:flutter/material.dart';

enum WindowHeaderPolicy { none, outer, inner }

class WindowPaneHeaderData {
  const WindowPaneHeaderData({
    required this.title,
    this.icon,
    this.policy = WindowHeaderPolicy.outer,
  });

  final String title;
  final IconData? icon;
  final WindowHeaderPolicy policy;
}
