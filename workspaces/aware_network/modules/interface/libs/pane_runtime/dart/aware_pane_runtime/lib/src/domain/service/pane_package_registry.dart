import 'package:flutter/widgets.dart';
import 'package:uuid/uuid_value.dart';

import 'package:aware_pane/aware_pane.dart' as runtime;

import '../../pane_kind.dart';
import '../../pane_system.dart';
import '../model/pane_factory.dart';

/// Explicit registrar signature for generated or package-owned Dart pane bundles.
typedef PanePackageRegistrar = void Function(PanePackageRegistry registry);

@immutable
class PanePackageRegistration {
  const PanePackageRegistration({
    required this.panePackageId,
    this.panePackageName,
    required this.paneKind,
    required this.factory,
    required this.capabilities,
    required this.displayInfo,
  });

  final UuidValue panePackageId;
  final String? panePackageName;
  final PaneKey paneKind;
  final PaneFactory factory;
  final runtime.PaneCapabilities capabilities;
  final runtime.PaneDisplayInfo displayInfo;
}

/// Parallel registry keyed by package-owned pane identity.
///
/// This coexists with the legacy `PaneRegistry` keyed by `PaneKey`. The purpose
/// here is to give generated pane-package registrars a stable Dart ABI target
/// before app-shell migration begins.
class PanePackageRegistry {
  final Map<String, PanePackageRegistration> _registrations = {};
  final List<String> _diagnostics = <String>[];

  void registerPanePackage({
    required UuidValue panePackageId,
    String? panePackageName,
    required PaneKey paneKind,
    required PaneFactory factory,
    required runtime.PaneCapabilities capabilities,
    runtime.PaneDisplayInfo? displayInfo,
  }) {
    final key = panePackageId.toString();
    if (_registrations.containsKey(key)) {
      _recordDiagnostic(
        'Duplicate pane package registration for "$key". Previous factory will be replaced.',
      );
    }
    _registrations[key] = PanePackageRegistration(
      panePackageId: panePackageId,
      panePackageName: panePackageName,
      paneKind: paneKind,
      factory: factory,
      capabilities: capabilities,
      displayInfo:
          displayInfo ??
          runtime.PaneDisplayInfo(
            paneKey: paneKind,
            title: panePackageName ?? paneKind,
            description: 'Pane package: ${panePackageName ?? paneKind}',
          ),
    );
  }

  void unregisterPanePackage(UuidValue panePackageId) {
    _registrations.remove(panePackageId.toString());
  }

  Widget? build(UuidValue panePackageId, PaneContext context) {
    final registration = registrationFor(panePackageId);
    if (registration == null) {
      return null;
    }
    return registration.factory(context.copyWith(kind: registration.paneKind));
  }

  PanePackageRegistration? registrationFor(UuidValue panePackageId) =>
      _registrations[panePackageId.toString()];

  runtime.PaneCapabilities? capabilitiesFor(UuidValue panePackageId) =>
      registrationFor(panePackageId)?.capabilities;

  runtime.PaneDisplayInfo? displayInfoFor(UuidValue panePackageId) =>
      registrationFor(panePackageId)?.displayInfo;

  bool isRegistered(UuidValue panePackageId) =>
      _registrations.containsKey(panePackageId.toString());

  List<UuidValue> registeredPanePackageIds() => _registrations.values
      .map((registration) => registration.panePackageId)
      .toList(growable: false);

  void clear() {
    _registrations.clear();
    _diagnostics.clear();
  }

  List<String> takeDiagnostics() {
    final snapshot = List<String>.from(_diagnostics);
    _diagnostics.clear();
    return snapshot;
  }

  void _recordDiagnostic(String message) {
    _diagnostics.add(message);
    assert(() {
      debugPrint('aware_pane_runtime: $message');
      return true;
    }());
  }
}
