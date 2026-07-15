import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'window_chrome_context.dart';

class WindowChromeState {
  const WindowChromeState({
    this.contributions = const {},
    this.sectionAggregates = const {},
  });

  /// Contributor id -> context.
  final Map<String, WindowChromeContext> contributions;

  /// Section id -> aggregated context.
  final Map<String, WindowChromeAggregateContext> sectionAggregates;

  WindowChromeState copyWith({
    Map<String, WindowChromeContext>? contributions,
    Map<String, WindowChromeAggregateContext>? sectionAggregates,
  }) {
    return WindowChromeState(
      contributions: contributions ?? this.contributions,
      sectionAggregates: sectionAggregates ?? this.sectionAggregates,
    );
  }
}

class WindowChromeController extends StateNotifier<WindowChromeState> {
  WindowChromeController() : super(const WindowChromeState());

  int _sequence = 0;
  final Map<String, int> _sequenceByContributorId = <String, int>{};

  void upsert(String contributorId, WindowChromeContext context) {
    final updated = Map<String, WindowChromeContext>.from(state.contributions)
      ..[contributorId] = context;
    _sequenceByContributorId[contributorId] = ++_sequence;
    state = state.copyWith(
      contributions: updated,
      sectionAggregates: _aggregateBySection(updated),
    );
  }

  void remove(String contributorId) {
    if (!state.contributions.containsKey(contributorId)) {
      return;
    }
    final updated = Map<String, WindowChromeContext>.from(state.contributions)
      ..remove(contributorId);
    _sequenceByContributorId.remove(contributorId);
    state = state.copyWith(
      contributions: updated,
      sectionAggregates: _aggregateBySection(updated),
    );
  }

  Map<String, WindowChromeAggregateContext> _aggregateBySection(
    Map<String, WindowChromeContext> contributions,
  ) {
    if (contributions.isEmpty) return const {};

    final grouped = <String, List<_ChromeContribution>>{};
    for (final entry in contributions.entries) {
      final contributorId = entry.key;
      final context = entry.value;
      (grouped[context.sectionId] ??= <_ChromeContribution>[]).add(
        _ChromeContribution(
          contributorId: contributorId,
          context: context,
          sequence: _sequenceByContributorId[contributorId] ?? 0,
        ),
      );
    }

    final aggregates = <String, WindowChromeAggregateContext>{};
    for (final entry in grouped.entries) {
      final aggregate = _aggregate(entry.value);
      if (aggregate != null) {
        aggregates[entry.key] = aggregate;
      }
    }
    return aggregates;
  }

  WindowChromeAggregateContext? _aggregate(
    Iterable<_ChromeContribution> contributions,
  ) {
    final list = contributions.toList();
    if (list.isEmpty) {
      return null;
    }
    list.sort((a, b) {
      final priority = b.priority.compareTo(a.priority);
      if (priority != 0) return priority;
      return b.sequence.compareTo(a.sequence);
    });

    final primary = list.first.context;

    String? title = primary.title;
    String? subtitle = primary.subtitle;
    if (title == null || subtitle == null) {
      for (final contribution in list.skip(1)) {
        title ??= contribution.context.title;
        subtitle ??= contribution.context.subtitle;
        if (title != null && subtitle != null) {
          break;
        }
      }
    }

    WindowChromeTheme? theme;
    for (final contribution in list) {
      if (contribution.context.theme != null) {
        theme = contribution.context.theme;
        break;
      }
    }

    List<ChromeBreadcrumb> breadcrumbs = List.of(primary.breadcrumbs);
    if (breadcrumbs.isEmpty) {
      breadcrumbs = list
          .skip(1)
          .map((contribution) => contribution.context.breadcrumbs)
          .expand((crumbs) => crumbs)
          .toList(growable: false);
    }

    List<ChromeBadge> badges = List.of(primary.badges);
    if (badges.isEmpty) {
      badges = list
          .skip(1)
          .map((contribution) => contribution.context.badges)
          .expand((badges) => badges)
          .toList(growable: false);
    }

    List<ChromeAction> actions = List.of(primary.actions);
    if (actions.isEmpty) {
      actions = list
          .skip(1)
          .map((contribution) => contribution.context.actions)
          .expand((actions) => actions)
          .toList(growable: false);
    }

    List<ChromeBadge> secondaryBadges = List.of(
      primary.secondary?.badges ?? const [],
    );
    if (secondaryBadges.isEmpty) {
      secondaryBadges = list
          .skip(1)
          .map(
            (contribution) =>
                contribution.context.secondary?.badges ?? const [],
          )
          .expand((badges) => badges)
          .toList(growable: false);
    }

    List<ChromeBreadcrumb> secondaryBreadcrumbs = List.of(
      primary.secondary?.breadcrumbs ?? const [],
    );
    if (secondaryBreadcrumbs.isEmpty) {
      secondaryBreadcrumbs = list
          .skip(1)
          .map(
            (contribution) =>
                contribution.context.secondary?.breadcrumbs ?? const [],
          )
          .expand((crumbs) => crumbs)
          .toList(growable: false);
    }

    ChromeMetadataModel metadata = const ChromeMetadataModel();
    for (final contribution in list) {
      metadata = metadata.mergeMissing(contribution.context.metadata);
    }

    // Fail open: if metadata isn't published, derive a minimal payload from
    // secondary badges/breadcrumbs so chrome popovers can remain informative.
    final fallbackMetadata = chromeBadgesToMetadata([
      ...secondaryBadges,
      ...secondaryBreadcrumbs.map((crumb) => ChromeBadge(label: crumb.label)),
    ]);
    metadata = metadata.mergeMissing(fallbackMetadata);

    ChromeNotification? notification;
    for (final contribution in list) {
      if (contribution.context.notification != null) {
        notification = contribution.context.notification;
        break;
      }
    }

    return WindowChromeAggregateContext(
      title: title,
      subtitle: subtitle,
      breadcrumbs: breadcrumbs,
      badges: badges,
      actions: actions,
      theme: theme,
      secondaryBadges: secondaryBadges,
      secondaryBreadcrumbs: secondaryBreadcrumbs,
      metadata: metadata,
      notification: notification,
    );
  }
}

final class _ChromeContribution {
  const _ChromeContribution({
    required this.contributorId,
    required this.context,
    required this.sequence,
  });

  final String contributorId;
  final WindowChromeContext context;
  final int sequence;

  int get priority => context.priority;
}

final windowChromeControllerProvider =
    StateNotifierProvider.family<
      WindowChromeController,
      WindowChromeState,
      String
    >((ref, windowId) {
      return WindowChromeController();
    });

/// Exposes the latest aggregated contexts keyed by section id for a window.
final windowChromeSectionAggregatesProvider =
    Provider.family<Map<String, WindowChromeAggregateContext>, String>((
      ref,
      windowId,
    ) {
      return ref
          .watch(windowChromeControllerProvider(windowId))
          .sectionAggregates;
    });

/// Read an aggregate chrome context for a specific (window, section).
final windowChromeSectionAggregateProvider =
    Provider.family<
      WindowChromeAggregateContext?,
      ({String windowId, String sectionId})
    >((ref, key) {
      final aggregates = ref.watch(
        windowChromeSectionAggregatesProvider(key.windowId),
      );
      return aggregates[key.sectionId];
    });

ChromeMetadataModel chromeBadgesToMetadata(List<ChromeBadge> badges) {
  if (badges.isEmpty) {
    return const ChromeMetadataModel();
  }
  final entries = badges
      .map(
        (badge) => ChromeMetadataEntry(
          label: badge.label,
          icon: badge.style?.icon,
          tooltip: badge.tooltip,
        ),
      )
      .toList(growable: false);
  return ChromeMetadataModel(custom: entries);
}
