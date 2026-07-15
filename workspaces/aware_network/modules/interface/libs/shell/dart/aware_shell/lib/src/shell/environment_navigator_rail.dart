import 'package:aware_environment_service_api/aware_environment_service_api.dart';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

class EnvironmentNavigatorTargetSelection {
  const EnvironmentNavigatorTargetSelection({
    this.environmentNavigationContextId,
    this.processId,
    this.threadId,
  });

  final String? environmentNavigationContextId;
  final String? processId;
  final String? threadId;
}

class EnvironmentNavigatorRail extends StatelessWidget {
  const EnvironmentNavigatorRail({
    required this.viewState,
    super.key,
    this.environmentNavigationContextId,
    this.onTargetSelected,
  });

  final EnvironmentNavigatorViewStateV1 viewState;
  final String? environmentNavigationContextId;
  final ValueChanged<EnvironmentNavigatorTargetSelection>? onTargetSelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Material(
      color: colors.surface.withValues(alpha: 0.92),
      elevation: 2,
      borderRadius: BorderRadius.circular(8),
      clipBehavior: Clip.antiAlias,
      child: SizedBox(
        width: 292,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 14, 14, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    viewState.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  _StatusLine(
                    status: viewState.status,
                    ready: viewState.ready == true,
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: viewState.processes.isEmpty
                  ? _EmptyNavigator(message: viewState.emptyMessage)
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: viewState.processes.length,
                      itemBuilder: (context, index) {
                        final process = viewState.processes[index];
                        return _ProcessTile(
                          process: process,
                          environmentNavigationContextId:
                              environmentNavigationContextId,
                          onTargetSelected: onTargetSelected,
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProcessTile extends StatelessWidget {
  const _ProcessTile({
    required this.process,
    required this.environmentNavigationContextId,
    required this.onTargetSelected,
  });

  final EnvironmentProcessNavigationItemV1 process;
  final String? environmentNavigationContextId;
  final ValueChanged<EnvironmentNavigatorTargetSelection>? onTargetSelected;

  @override
  Widget build(BuildContext context) {
    final selected = process.isSelected == true;
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: selected
              ? colors.primaryContainer.withValues(alpha: 0.32)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: selected
                ? colors.primary.withValues(alpha: 0.5)
                : colors.outlineVariant.withValues(alpha: 0.45),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            InkWell(
              borderRadius: BorderRadius.circular(8),
              onTap: _selectProcess,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(10, 9, 10, 8),
                child: Row(
                  children: [
                    Icon(
                      selected ? Icons.folder_open : Icons.folder_outlined,
                      size: 17,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        process.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: selected
                              ? FontWeight.w700
                              : FontWeight.w600,
                        ),
                      ),
                    ),
                    Text(
                      '${process.threadCount}',
                      style: theme.textTheme.labelSmall,
                    ),
                  ],
                ),
              ),
            ),
            for (final thread in process.threads)
              _ThreadTile(
                process: process,
                thread: thread,
                environmentNavigationContextId: environmentNavigationContextId,
                onTargetSelected: onTargetSelected,
              ),
          ],
        ),
      ),
    );
  }

  void _selectProcess() {
    final processId = _uuidStringOrNull(process.processId);
    if (processId == null) {
      return;
    }
    onTargetSelected?.call(
      EnvironmentNavigatorTargetSelection(
        environmentNavigationContextId: environmentNavigationContextId,
        processId: processId,
      ),
    );
  }
}

class _ThreadTile extends StatelessWidget {
  const _ThreadTile({
    required this.process,
    required this.thread,
    required this.environmentNavigationContextId,
    required this.onTargetSelected,
  });

  final EnvironmentProcessNavigationItemV1 process;
  final EnvironmentThreadNavigationItemV1 thread;
  final String? environmentNavigationContextId;
  final ValueChanged<EnvironmentNavigatorTargetSelection>? onTargetSelected;

  @override
  Widget build(BuildContext context) {
    final selected = thread.isSelected == true;
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return InkWell(
      onTap: _selectThread,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(34, 7, 10, 7),
        child: Row(
          children: [
            Icon(
              selected ? Icons.chat_bubble : Icons.chat_bubble_outline,
              size: 15,
              color: selected ? colors.primary : colors.onSurfaceVariant,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                thread.title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodySmall?.copyWith(
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _selectThread() {
    final processId = _uuidStringOrNull(process.processId);
    final threadId = _uuidStringOrNull(thread.threadId);
    if (processId == null && threadId == null) {
      return;
    }
    onTargetSelected?.call(
      EnvironmentNavigatorTargetSelection(
        environmentNavigationContextId: environmentNavigationContextId,
        processId: processId,
        threadId: threadId,
      ),
    );
  }
}

class _StatusLine extends StatelessWidget {
  const _StatusLine({required this.status, required this.ready});

  final String status;
  final bool ready;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;
    return Row(
      children: [
        Icon(
          ready ? Icons.check_circle_outline : Icons.info_outline,
          size: 14,
          color: ready ? colors.primary : colors.onSurfaceVariant,
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            status,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: theme.textTheme.labelSmall?.copyWith(
              color: colors.onSurfaceVariant,
            ),
          ),
        ),
      ],
    );
  }
}

class _EmptyNavigator extends StatelessWidget {
  const _EmptyNavigator({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Text(
          message,
          textAlign: TextAlign.center,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

String? _uuidStringOrNull(UuidValue? value) {
  final text = value?.uuid.trim();
  if (text == null || text.isEmpty) {
    return null;
  }
  return text;
}
