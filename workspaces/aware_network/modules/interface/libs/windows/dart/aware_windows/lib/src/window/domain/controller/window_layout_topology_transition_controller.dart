import 'dart:async';

import 'package:flutter/widgets.dart';

@immutable
class WindowLayoutTopologyCatalogSection {
  const WindowLayoutTopologyCatalogSection({
    required this.sectionId,
    required this.catalogOrder,
  });

  final String sectionId;
  final int catalogOrder;
}

@immutable
class WindowLayoutTopologyCommitSectionState {
  const WindowLayoutTopologyCommitSectionState({
    required this.sectionId,
    required this.order,
  });

  final String sectionId;
  final int order;
}

@immutable
class WindowLayoutTopologyCommitIntent {
  const WindowLayoutTopologyCommitIntent({
    required this.clientIntentId,
    required this.expectedPreviousTopologyTransitionId,
    required this.sectionStates,
  });

  final String clientIntentId;
  final String? expectedPreviousTopologyTransitionId;
  final List<WindowLayoutTopologyCommitSectionState> sectionStates;
}

typedef WindowLayoutTopologyCommitCallback =
    Future<void> Function(WindowLayoutTopologyCommitIntent intent);

class WindowLayoutTopologyScope
    extends InheritedNotifier<WindowLayoutTopologyTransitionController> {
  const WindowLayoutTopologyScope({
    required WindowLayoutTopologyTransitionController controller,
    required super.child,
    super.key,
  }) : super(notifier: controller);

  static WindowLayoutTopologyTransitionController? maybeOf(
    BuildContext context,
  ) => context
      .dependOnInheritedWidgetOfExactType<WindowLayoutTopologyScope>()
      ?.notifier;

  static WindowLayoutTopologyTransitionController of(BuildContext context) {
    final controller = maybeOf(context);
    assert(
      controller != null,
      'No WindowLayoutTopologyScope found in context.',
    );
    return controller!;
  }
}

/// Owns transient membership/order preview over a stable admitted catalog.
///
/// Removing a section only removes it from [activeSectionIds]. The admitted
/// catalog remains intact so the same stable anchor can be re-added. Committed
/// truth enters only through [reconcile].
class WindowLayoutTopologyTransitionController extends ChangeNotifier {
  WindowLayoutTopologyTransitionController({
    required List<WindowLayoutTopologyCatalogSection> admittedSections,
    required List<String> committedActiveSectionIds,
    required String Function() clientIntentIdFactory,
    required WindowLayoutTopologyCommitCallback onCommit,
    String? committedTopologyTransitionId,
  }) : _clientIntentIdFactory = clientIntentIdFactory,
       _onCommit = onCommit {
    _replaceCommitted(
      admittedSections: admittedSections,
      activeSectionIds: committedActiveSectionIds,
      topologyTransitionId: committedTopologyTransitionId,
    );
  }

  final String Function() _clientIntentIdFactory;
  final WindowLayoutTopologyCommitCallback _onCommit;

  List<WindowLayoutTopologyCatalogSection> _admittedSections = const [];
  List<String> _committedActiveSectionIds = const [];
  List<String> _previewActiveSectionIds = const [];
  String? _committedTopologyTransitionId;
  String? _previewExpectedTopologyTransitionId;
  bool _previewing = false;
  bool _commitInFlight = false;

  List<WindowLayoutTopologyCatalogSection> get admittedSections =>
      List<WindowLayoutTopologyCatalogSection>.unmodifiable(_admittedSections);
  List<String> get activeSectionIds =>
      List<String>.unmodifiable(_previewActiveSectionIds);
  String? get committedTopologyTransitionId => _committedTopologyTransitionId;
  bool get previewing => _previewing;
  bool get commitInFlight => _commitInFlight;

  void reconcile({
    required List<WindowLayoutTopologyCatalogSection> admittedSections,
    required List<String> committedActiveSectionIds,
    required String? committedTopologyTransitionId,
  }) {
    _replaceCommitted(
      admittedSections: admittedSections,
      activeSectionIds: committedActiveSectionIds,
      topologyTransitionId: committedTopologyTransitionId,
    );
    notifyListeners();
  }

  void beginPreview() {
    if (_previewing || _commitInFlight) {
      return;
    }
    _previewActiveSectionIds = [..._committedActiveSectionIds];
    _previewExpectedTopologyTransitionId = _committedTopologyTransitionId;
    _previewing = true;
    notifyListeners();
  }

  void previewRemove(String sectionId) {
    if (!_previewing) {
      beginPreview();
    }
    if (_previewActiveSectionIds.length <= 1) {
      return;
    }
    if (_previewActiveSectionIds.remove(sectionId)) {
      notifyListeners();
    }
  }

  void previewReadd(String sectionId, {int? atIndex}) {
    if (!_previewing) {
      beginPreview();
    }
    if (!_admittedIds.contains(sectionId) ||
        _previewActiveSectionIds.contains(sectionId)) {
      return;
    }
    final index = (atIndex ?? _previewActiveSectionIds.length)
        .clamp(0, _previewActiveSectionIds.length)
        .toInt();
    _previewActiveSectionIds.insert(index, sectionId);
    notifyListeners();
  }

  void previewMove(String sectionId, int toIndex) {
    if (!_previewing) {
      beginPreview();
    }
    final fromIndex = _previewActiveSectionIds.indexOf(sectionId);
    if (fromIndex < 0) {
      return;
    }
    final target = toIndex
        .clamp(0, _previewActiveSectionIds.length - 1)
        .toInt();
    if (fromIndex == target) {
      return;
    }
    _previewActiveSectionIds.removeAt(fromIndex);
    _previewActiveSectionIds.insert(target, sectionId);
    notifyListeners();
  }

  void cancelPreview() {
    if (!_previewing && !_commitInFlight) {
      return;
    }
    _previewActiveSectionIds = [..._committedActiveSectionIds];
    _previewExpectedTopologyTransitionId = null;
    _previewing = false;
    _commitInFlight = false;
    notifyListeners();
  }

  Future<void> commitPreview() async {
    if (!_previewing || _commitInFlight) {
      return;
    }
    final intent = WindowLayoutTopologyCommitIntent(
      clientIntentId: _clientIntentIdFactory(),
      expectedPreviousTopologyTransitionId:
          _previewExpectedTopologyTransitionId,
      sectionStates: [
        for (var index = 0; index < _previewActiveSectionIds.length; index += 1)
          WindowLayoutTopologyCommitSectionState(
            sectionId: _previewActiveSectionIds[index],
            order: index,
          ),
      ],
    );
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

  Set<String> get _admittedIds => {
    for (final section in _admittedSections) section.sectionId,
  };

  void _replaceCommitted({
    required List<WindowLayoutTopologyCatalogSection> admittedSections,
    required List<String> activeSectionIds,
    required String? topologyTransitionId,
  }) {
    final orderedCatalog = [...admittedSections]
      ..sort((a, b) {
        final byOrder = a.catalogOrder.compareTo(b.catalogOrder);
        return byOrder != 0 ? byOrder : a.sectionId.compareTo(b.sectionId);
      });
    final admittedIds = <String>{};
    final catalogOrders = <int>{};
    for (final section in orderedCatalog) {
      if (section.sectionId.trim().isEmpty ||
          !admittedIds.add(section.sectionId) ||
          section.catalogOrder < 0 ||
          !catalogOrders.add(section.catalogOrder)) {
        throw ArgumentError(
          'Admitted section ids and catalog orders must be unique and valid.',
        );
      }
    }
    if (orderedCatalog.isEmpty) {
      throw ArgumentError('Admitted section catalog must be non-empty.');
    }
    final activeIds = <String>{};
    for (final sectionId in activeSectionIds) {
      if (!admittedIds.contains(sectionId) || !activeIds.add(sectionId)) {
        throw ArgumentError(
          'Active membership must be a unique subset of admitted sections.',
        );
      }
    }
    if (activeSectionIds.isEmpty) {
      throw ArgumentError('At least one admitted section must remain active.');
    }
    _admittedSections = orderedCatalog;
    _committedActiveSectionIds = [...activeSectionIds];
    _previewActiveSectionIds = [...activeSectionIds];
    _committedTopologyTransitionId = topologyTransitionId;
    _previewExpectedTopologyTransitionId = null;
    _previewing = false;
    _commitInFlight = false;
  }
}
