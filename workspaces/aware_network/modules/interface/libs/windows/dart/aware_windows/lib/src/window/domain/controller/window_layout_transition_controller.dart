import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';

const int windowLayoutWeightMicrosTotal = 1000000;

@immutable
class WindowLayoutSectionVectorState {
  const WindowLayoutSectionVectorState({
    required this.sectionId,
    required this.order,
    required this.weight,
    this.weightMicros,
    this.isVisible = true,
    this.isCollapsed = false,
  });

  final String sectionId;
  final int order;
  final double weight;
  final int? weightMicros;
  final bool isVisible;
  final bool isCollapsed;

  bool get isActive => isVisible && !isCollapsed;

  WindowLayoutSectionVectorState copyWith({
    int? order,
    double? weight,
    int? weightMicros,
    bool clearWeightMicros = false,
    bool? isVisible,
    bool? isCollapsed,
  }) {
    return WindowLayoutSectionVectorState(
      sectionId: sectionId,
      order: order ?? this.order,
      weight: weight ?? this.weight,
      weightMicros: clearWeightMicros
          ? null
          : (weightMicros ?? this.weightMicros),
      isVisible: isVisible ?? this.isVisible,
      isCollapsed: isCollapsed ?? this.isCollapsed,
    );
  }
}

@immutable
class WindowLayoutTransitionCommitSectionState {
  const WindowLayoutTransitionCommitSectionState({
    required this.sectionId,
    required this.order,
    required this.weightMicros,
    required this.isVisible,
    required this.isCollapsed,
  });

  final String sectionId;
  final int order;
  final int weightMicros;
  final bool isVisible;
  final bool isCollapsed;
}

@immutable
class WindowLayoutTransitionCommitIntent {
  const WindowLayoutTransitionCommitIntent({
    required this.clientIntentId,
    required this.expectedPreviousTransitionId,
    required this.topologyTransitionId,
    required this.sectionStates,
  });

  final String clientIntentId;
  final String? expectedPreviousTransitionId;
  final String? topologyTransitionId;
  final List<WindowLayoutTransitionCommitSectionState> sectionStates;
}

typedef WindowLayoutTransitionCommitCallback =
    Future<void> Function(WindowLayoutTransitionCommitIntent intent);

/// Owns transient renderer preview only; committed truth always enters through
/// [reconcile]. Network mutation occurs exactly once in [commitPreview].
class WindowLayoutTransitionController extends ChangeNotifier {
  WindowLayoutTransitionController({
    required List<WindowLayoutSectionVectorState> committedSections,
    required String Function() clientIntentIdFactory,
    required WindowLayoutTransitionCommitCallback onCommit,
    String? committedTransitionId,
    String? committedTopologyTransitionId,
  }) : _clientIntentIdFactory = clientIntentIdFactory,
       _onCommit = onCommit {
    _replaceCommitted(
      committedSections,
      committedTransitionId: committedTransitionId,
      committedTopologyTransitionId: committedTopologyTransitionId,
    );
  }

  final String Function() _clientIntentIdFactory;
  final WindowLayoutTransitionCommitCallback _onCommit;

  List<WindowLayoutSectionVectorState> _committedSections = const [];
  List<WindowLayoutSectionVectorState> _previewSections = const [];
  String? _committedTransitionId;
  String? _committedTopologyTransitionId;
  String? _previewExpectedTransitionId;
  String? _previewTopologyTransitionId;
  bool _previewing = false;
  bool _commitInFlight = false;

  List<WindowLayoutSectionVectorState> get sections =>
      List<WindowLayoutSectionVectorState>.unmodifiable(_previewSections);
  String? get committedTransitionId => _committedTransitionId;
  String? get committedTopologyTransitionId => _committedTopologyTransitionId;
  bool get previewing => _previewing;
  bool get commitInFlight => _commitInFlight;

  void reconcile({
    required List<WindowLayoutSectionVectorState> committedSections,
    required String? committedTransitionId,
    String? committedTopologyTransitionId,
  }) {
    _replaceCommitted(
      committedSections,
      committedTransitionId: committedTransitionId,
      committedTopologyTransitionId: committedTopologyTransitionId,
    );
    notifyListeners();
  }

  void beginPreview() {
    if (_commitInFlight || _previewing) {
      return;
    }
    _previewSections = _copySections(_committedSections);
    _previewExpectedTransitionId = _committedTransitionId;
    _previewTopologyTransitionId = _committedTopologyTransitionId;
    _previewing = true;
    notifyListeners();
  }

  void previewResizeGroups({
    required Set<String> leadingSectionIds,
    required Set<String> trailingSectionIds,
    required double deltaFraction,
  }) {
    if (!_previewing || !deltaFraction.isFinite || deltaFraction == 0) {
      return;
    }
    final leading = _activeIndexes(leadingSectionIds);
    final trailing = _activeIndexes(trailingSectionIds);
    if (leading.isEmpty || trailing.isEmpty) {
      return;
    }
    final leadingWeight = _weightForIndexes(leading);
    final trailingWeight = _weightForIndexes(trailing);
    final combinedWeight = leadingWeight + trailingWeight;
    if (combinedWeight <= 0) {
      return;
    }
    const minimumGroupWeight = 0.000001;
    final nextLeading = (leadingWeight + deltaFraction).clamp(
      minimumGroupWeight,
      combinedWeight - minimumGroupWeight,
    );
    final nextTrailing = combinedWeight - nextLeading;
    _scaleIndexes(leading, fromWeight: leadingWeight, toWeight: nextLeading);
    _scaleIndexes(trailing, fromWeight: trailingWeight, toWeight: nextTrailing);
    notifyListeners();
  }

  void previewToggleCollapse(String sectionId) {
    if (!_previewing) {
      beginPreview();
    }
    final index = _previewSections.indexWhere(
      (section) => section.sectionId == sectionId,
    );
    if (index < 0) {
      return;
    }
    final current = _previewSections[index];
    if (!current.isVisible) {
      return;
    }
    final others = <int>[
      for (
        var candidate = 0;
        candidate < _previewSections.length;
        candidate += 1
      )
        if (candidate != index && _previewSections[candidate].isActive)
          candidate,
    ];
    if (others.isEmpty) {
      return;
    }
    if (!current.isCollapsed) {
      final released = math.max(0.0, current.weight);
      _previewSections[index] = current.copyWith(
        weight: 0,
        clearWeightMicros: true,
        isCollapsed: true,
      );
      _distributeAddedWeight(others, released);
    } else {
      final committed = _committedSections.firstWhere(
        (section) => section.sectionId == sectionId,
        orElse: () => current,
      );
      final requested = math.max(
        0.000001,
        committed.weight > 0 ? committed.weight : 1 / _previewSections.length,
      );
      final available = _weightForIndexes(others);
      final reopened = math.min(requested, available - 0.000001);
      if (reopened <= 0) {
        return;
      }
      _scaleIndexes(
        others,
        fromWeight: available,
        toWeight: available - reopened,
      );
      _previewSections[index] = current.copyWith(
        weight: reopened,
        clearWeightMicros: true,
        isCollapsed: false,
      );
    }
    notifyListeners();
  }

  void cancelPreview() {
    if (!_previewing && !_commitInFlight) {
      return;
    }
    _previewSections = _copySections(_committedSections);
    _previewExpectedTransitionId = null;
    _previewTopologyTransitionId = null;
    _previewing = false;
    _commitInFlight = false;
    notifyListeners();
  }

  Future<void> commitPreview() async {
    if (!_previewing || _commitInFlight) {
      return;
    }
    final quantized = quantizeSections(_previewSections);
    final intent = WindowLayoutTransitionCommitIntent(
      clientIntentId: _clientIntentIdFactory(),
      expectedPreviousTransitionId: _previewExpectedTransitionId,
      topologyTransitionId: _previewTopologyTransitionId,
      sectionStates: quantized,
    );
    final quantizedById = {
      for (final section in quantized) section.sectionId: section,
    };
    _previewSections = [
      for (final section in _previewSections)
        if (quantizedById[section.sectionId] case final committed?)
          section.copyWith(
            weight: committed.weightMicros / windowLayoutWeightMicrosTotal,
            weightMicros: committed.weightMicros,
            isVisible: committed.isVisible,
            isCollapsed: committed.isCollapsed,
          )
        else
          section,
    ];
    _previewing = false;
    _commitInFlight = true;
    notifyListeners();
    try {
      await _onCommit(intent);
    } catch (_) {
      cancelPreview();
      rethrow;
    } finally {
      if (_commitInFlight) {
        _commitInFlight = false;
        notifyListeners();
      }
    }
  }

  static List<WindowLayoutTransitionCommitSectionState> quantizeSections(
    List<WindowLayoutSectionVectorState> sections,
  ) {
    if (sections.isEmpty) {
      throw ArgumentError.value(sections, 'sections', 'must be non-empty');
    }
    final ordered = [...sections]
      ..sort((a, b) {
        final byOrder = a.order.compareTo(b.order);
        return byOrder != 0 ? byOrder : a.sectionId.compareTo(b.sectionId);
      });
    final seenIds = <String>{};
    final seenOrders = <int>{};
    for (final section in ordered) {
      if (section.sectionId.trim().isEmpty ||
          !seenIds.add(section.sectionId) ||
          section.order < 0 ||
          !seenOrders.add(section.order)) {
        throw ArgumentError('Section ids and orders must be unique and valid.');
      }
    }
    if (seenOrders.length != ordered.length ||
        !seenOrders.containsAll(Iterable<int>.generate(ordered.length))) {
      throw ArgumentError('Section orders must be contiguous from zero.');
    }
    final active = ordered.where((section) => section.isActive).toList();
    if (active.isEmpty) {
      throw ArgumentError('At least one section must remain active.');
    }
    if (active.length > windowLayoutWeightMicrosTotal) {
      throw ArgumentError(
        'Active sections exceed the positive-micros allocation capacity.',
      );
    }
    final total = active.fold<double>(
      0,
      (sum, section) => sum + math.max(0, section.weight),
    );
    if (!total.isFinite || total <= 0) {
      throw ArgumentError('Active section weights must have a positive sum.');
    }

    final microsById = <String, int>{};
    final remainders = <({String id, int order, double fraction})>[];
    // Every active ontology row requires a positive integer weight. Reserve one
    // micro first, then distribute the remaining budget by largest remainder.
    final distributable = windowLayoutWeightMicrosTotal - active.length;
    var allocated = active.length;
    for (final section in active) {
      final exact = math.max(0, section.weight) / total * distributable;
      final floorValue = exact.floor();
      microsById[section.sectionId] = floorValue + 1;
      allocated += floorValue;
      remainders.add((
        id: section.sectionId,
        order: section.order,
        fraction: exact - floorValue,
      ));
    }
    remainders.sort((a, b) {
      final byFraction = b.fraction.compareTo(a.fraction);
      if (byFraction != 0) {
        return byFraction;
      }
      final byOrder = a.order.compareTo(b.order);
      return byOrder != 0 ? byOrder : a.id.compareTo(b.id);
    });
    final remainder = windowLayoutWeightMicrosTotal - allocated;
    for (var index = 0; index < remainder; index += 1) {
      final target = remainders[index % remainders.length];
      microsById[target.id] = (microsById[target.id] ?? 0) + 1;
    }

    return [
      for (final section in ordered)
        WindowLayoutTransitionCommitSectionState(
          sectionId: section.sectionId,
          order: section.order,
          weightMicros: section.isActive
              ? (microsById[section.sectionId] ?? 0)
              : 0,
          isVisible: section.isVisible,
          isCollapsed: section.isCollapsed,
        ),
    ];
  }

  void _replaceCommitted(
    List<WindowLayoutSectionVectorState> sections, {
    required String? committedTransitionId,
    required String? committedTopologyTransitionId,
  }) {
    _committedSections = _copySections(sections);
    _previewSections = _copySections(sections);
    _committedTransitionId = committedTransitionId;
    _committedTopologyTransitionId = committedTopologyTransitionId;
    _previewExpectedTransitionId = null;
    _previewTopologyTransitionId = null;
    _previewing = false;
    _commitInFlight = false;
  }

  List<int> _activeIndexes(Set<String> ids) {
    return <int>[
      for (var index = 0; index < _previewSections.length; index += 1)
        if (ids.contains(_previewSections[index].sectionId) &&
            _previewSections[index].isActive)
          index,
    ];
  }

  double _weightForIndexes(List<int> indexes) {
    return indexes.fold<double>(
      0,
      (sum, index) => sum + math.max(0, _previewSections[index].weight),
    );
  }

  void _scaleIndexes(
    List<int> indexes, {
    required double fromWeight,
    required double toWeight,
  }) {
    if (indexes.isEmpty) {
      return;
    }
    if (fromWeight <= 0) {
      final each = toWeight / indexes.length;
      for (final index in indexes) {
        _previewSections[index] = _previewSections[index].copyWith(
          weight: each,
          clearWeightMicros: true,
        );
      }
      return;
    }
    final scale = toWeight / fromWeight;
    for (final index in indexes) {
      _previewSections[index] = _previewSections[index].copyWith(
        weight: math.max(0, _previewSections[index].weight) * scale,
        clearWeightMicros: true,
      );
    }
  }

  void _distributeAddedWeight(List<int> indexes, double addedWeight) {
    if (addedWeight <= 0 || indexes.isEmpty) {
      return;
    }
    final current = _weightForIndexes(indexes);
    _scaleIndexes(
      indexes,
      fromWeight: current,
      toWeight: current + addedWeight,
    );
  }

  static List<WindowLayoutSectionVectorState> _copySections(
    List<WindowLayoutSectionVectorState> sections,
  ) {
    return [
      for (final section in sections)
        section.copyWith(
          weight: section.weight,
          weightMicros: section.weightMicros,
        ),
    ];
  }
}
