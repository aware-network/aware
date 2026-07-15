import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_header_data.dart';
import '../../domain/provider/window_header_provider.dart';

class WindowHeaderBar extends ConsumerWidget {
  const WindowHeaderBar({super.key, required this.headerArgs});

  final HeaderControllerArgs headerArgs;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(windowHeaderControllerProvider(headerArgs));
    final data = state.active;
    final theme = Theme.of(context);
    final textColor = data.accentColor ?? theme.colorScheme.onSurface;
    final actions = [
      ...data.leadingActions.map(
        (action) => _buildActionButton(context, ref, action),
      ),
      ...data.trailingActions.map(
        (action) => _buildActionButton(context, ref, action),
      ),
    ];

    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: theme.cardColor,
        border: Border(
          bottom: BorderSide(color: theme.dividerColor.withValues(alpha: 0.4)),
        ),
      ),
      child: Row(
        children: [
          if (data.icon != null) ...[
            Icon(data.icon, size: 18, color: textColor.withValues(alpha: 0.8)),
            const SizedBox(width: 8),
          ],
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  data.title,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: textColor,
                  ),
                ),
                if (data.subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    data.subtitle!,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: textColor.withValues(alpha: 0.7),
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (actions.isNotEmpty) ...[
            const SizedBox(width: 8),
            Flexible(
              child: Wrap(
                spacing: 4,
                runSpacing: 4,
                alignment: WrapAlignment.end,
                children: actions,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildActionButton(
    BuildContext context,
    WidgetRef ref,
    WindowHeaderAction action,
  ) {
    final theme = Theme.of(context);
    final color = action.foregroundColor ?? theme.iconTheme.color;
    final iconButton = IconButton(
      icon: Icon(
        action.icon,
        color: action.isActive
            ? (action.foregroundColor ?? theme.colorScheme.primary)
            : color,
      ),
      iconSize: action.iconSize ?? theme.iconTheme.size ?? 24,
      tooltip: action.tooltip,
      onPressed: action.enabled ? () => action.onPressed(ref) : null,
    );

    if (action.badgeLabel != null) {
      return Badge(label: Text(action.badgeLabel!), child: iconButton);
    }

    return iconButton;
  }
}
