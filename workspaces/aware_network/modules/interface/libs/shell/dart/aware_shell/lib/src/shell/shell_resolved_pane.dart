import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:uuid/uuid_value.dart';

class InterfaceShellResolvedPane {
  const InterfaceShellResolvedPane({
    required this.windowKey,
    required this.layoutKey,
    required this.sectionKey,
    required this.paneKind,
    required this.stateSourceKind,
    this.layoutConfigSectionConfigId,
    this.layoutSectionId,
    this.sectionFocusScopeId,
    this.focusScopeId,
    this.branchId,
    this.paneConfigId,
    this.panePackageId,
    this.panePackageName,
    this.projectionViewId,
    this.viewRef,
    this.projectionViewKey,
    this.title,
    this.summary,
    this.narrativeKey,
    this.stateProjectionHash,
    this.apiCapabilityEndpointIds = const <UuidValue>[],
    this.actionKeys = const <String>[],
  });

  factory InterfaceShellResolvedPane.fromDescriptor(
    InterfaceResolvedPaneDescriptor descriptor,
  ) {
    return InterfaceShellResolvedPane(
      windowKey: descriptor.windowKey,
      layoutKey: descriptor.layoutKey,
      sectionKey: descriptor.sectionKey,
      layoutConfigSectionConfigId: descriptor.layoutConfigSectionConfigId,
      layoutSectionId: descriptor.layoutSectionId,
      sectionFocusScopeId: descriptor.sectionFocusScopeId,
      focusScopeId: descriptor.focusScopeId,
      branchId: descriptor.branchId,
      paneKind: descriptor.paneKind,
      paneConfigId: descriptor.paneConfigId,
      panePackageId: descriptor.panePackageId,
      panePackageName: descriptor.panePackageName,
      projectionViewId: descriptor.projectionViewId,
      viewRef: descriptor.viewRef,
      projectionViewKey: descriptor.projectionViewKey,
      title: descriptor.title,
      summary: descriptor.summary,
      narrativeKey: descriptor.narrativeKey,
      stateSourceKind: descriptor.stateSourceKind,
      stateProjectionHash: descriptor.stateProjectionHash,
      actionKeys: descriptor.actionKeys,
    );
  }

  final String windowKey;
  final String layoutKey;
  final String sectionKey;
  final UuidValue? layoutConfigSectionConfigId;
  final UuidValue? layoutSectionId;
  final UuidValue? sectionFocusScopeId;
  final UuidValue? focusScopeId;
  final UuidValue? branchId;
  final String paneKind;
  final UuidValue? paneConfigId;
  final UuidValue? panePackageId;
  final String? panePackageName;
  final String? projectionViewId;
  final String? viewRef;
  final String? projectionViewKey;
  final String? title;
  final String? summary;
  final String? narrativeKey;
  final String stateSourceKind;
  final String? stateProjectionHash;
  final List<UuidValue> apiCapabilityEndpointIds;
  final List<String> actionKeys;
}
