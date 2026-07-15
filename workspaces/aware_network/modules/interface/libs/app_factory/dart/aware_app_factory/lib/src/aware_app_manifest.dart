import 'package:aware_shell/aware_shell.dart' as shell;
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

typedef AwareInterfaceRuntimeFactory = shell.InterfacePackageRuntime Function();

@immutable
class AwareInterfaceRuntimeRegistration {
  const AwareInterfaceRuntimeRegistration({
    required this.interfacePackageId,
    required this.interfacePackageName,
    required this.buildRuntime,
  });

  final String interfacePackageId;
  final String interfacePackageName;
  final AwareInterfaceRuntimeFactory buildRuntime;
}

@immutable
class AwareAppRuntimeCatalog {
  const AwareAppRuntimeCatalog({required this.registrations});

  final List<AwareInterfaceRuntimeRegistration> registrations;

  shell.InterfacePackageRuntimeRegistry buildRuntimeRegistry() {
    final registry = shell.InterfacePackageRuntimeRegistry();
    for (final registration in registrations) {
      registry.register(registration.buildRuntime());
    }
    return registry;
  }

  List<String> interfacePackageNames() {
    return registrations
        .map((registration) => registration.interfacePackageName)
        .toList(growable: false);
  }
}

@immutable
class AwareAppComposition {
  const AwareAppComposition({
    required this.appId,
    required this.displayName,
    this.seedColorValue = 0xFF2563EB,
    this.controlPolicy = const AwareAppControlPolicy(),
  });

  final String appId;
  final String displayName;
  final int seedColorValue;
  final AwareAppControlPolicy controlPolicy;
}

@immutable
class AwareAppControlPolicy {
  const AwareAppControlPolicy({
    this.requiresActor = true,
    this.defaultScreenKey = 'control',
    this.admittedScreenKey,
  });

  final bool requiresActor;
  final String defaultScreenKey;
  final String? admittedScreenKey;
}

@immutable
class AwareAppPackageEvidence {
  const AwareAppPackageEvidence({
    required this.packageName,
    required this.appPackageId,
    required this.branchId,
    required this.objectInstanceGraphCommitId,
  });

  final String packageName;
  final String appPackageId;
  final String branchId;
  final String objectInstanceGraphCommitId;

  Map<String, dynamic> toEvidence() {
    return <String, dynamic>{
      'package_name': packageName,
      'app_package_id': appPackageId,
      'branch_id': branchId,
      'object_instance_graph_commit_id': objectInstanceGraphCommitId,
    };
  }
}

typedef AwareAppCanonicalRenderSpecActionDispatcher = Future<void> Function(
    shell.PaneRenderActionInvocation invocation);

typedef AwareAppCommittedScreenEnterer = Future<void> Function(
  AwareAppPackageEvidence appPackage,
  AwareAppCommittedScreen screen,
  shell.PaneRenderActionInvocation invocation,
  Map<String, dynamic> evidence,
);

Future<void> dispatchAwareAppRenderSpecAction({
  required shell.PaneRenderActionInvocation invocation,
  required AwareAppPackageEvidence appPackage,
  required AwareAppCommittedScreen? committedScreen,
  required AwareAppCanonicalRenderSpecActionDispatcher dispatchCanonicalAction,
  required AwareAppCommittedScreenEnterer enterCommittedScreen,
}) async {
  await dispatchCanonicalAction(invocation);
  final screen = committedScreen;
  if (!isAwareAppControlAdmissionAction(invocation, screen)) {
    return;
  }
  await enterCommittedScreen(
    appPackage,
    screen!,
    invocation,
    awareAppScreenEntryEvidence(
      appPackage: appPackage,
      screen: screen,
      invocation: invocation,
    ),
  );
}

bool isAwareAppControlAdmissionAction(
  shell.PaneRenderActionInvocation invocation,
  AwareAppCommittedScreen? committedScreen,
) {
  return committedScreen != null && invocation.actionKey == 'admit_identity';
}

Map<String, dynamic> awareAppScreenEntryEvidence({
  required AwareAppPackageEvidence appPackage,
  required AwareAppCommittedScreen screen,
  required shell.PaneRenderActionInvocation invocation,
}) {
  return <String, dynamic>{
    'aware_app_package': appPackage.toEvidence(),
    'aware_app_screen': screen.toEvidence(),
    'control_action_key': invocation.actionKey,
    'control_action_kind': invocation.actionKind,
    'control_action_payload': invocation.payload,
  };
}

@immutable
class AwareAppSessionAuthority {
  const AwareAppSessionAuthority({
    required this.screenAccepted,
    required this.committedEvidenceMatches,
    required this.experienceLensReady,
    this.blockedReason,
  });

  const AwareAppSessionAuthority.notRequired()
      : screenAccepted = true,
        committedEvidenceMatches = true,
        experienceLensReady = false,
        blockedReason = null;

  factory AwareAppSessionAuthority.fromHostState(
    shell.InterfaceHostState? hostState, {
    required AwareAppPackageEvidence appPackage,
    required AwareAppCommittedScreen screen,
    String? failureMessage,
  }) {
    if (failureMessage != null && failureMessage.trim().isNotEmpty) {
      return AwareAppSessionAuthority(
        screenAccepted: false,
        committedEvidenceMatches: false,
        experienceLensReady: false,
        blockedReason: failureMessage.trim(),
      );
    }
    final appScreen = hostState?.appScreen;
    final screenAccepted = appScreen?.accepted == true;
    final committedEvidenceMatches = screenAccepted &&
        _uuidMatches(appScreen?.appPackageId, appPackage.appPackageId) &&
        _uuidMatches(appScreen?.appPackageBranchId, appPackage.branchId) &&
        _uuidMatches(
          appScreen?.appPackageObjectInstanceGraphCommitId,
          appPackage.objectInstanceGraphCommitId,
        ) &&
        _uuidMatches(
          appScreen?.appConfigScreenConfigId,
          screen.appConfigScreenConfigId,
        );
    final experienceLensReady = hostState?.experienceLens != null;
    final blockedReason = _screenAuthorityBlockedReason(
      hostState: hostState,
      screenAccepted: screenAccepted,
      committedEvidenceMatches: committedEvidenceMatches,
    );
    return AwareAppSessionAuthority(
      screenAccepted: screenAccepted,
      committedEvidenceMatches: committedEvidenceMatches,
      experienceLensReady: experienceLensReady,
      blockedReason: blockedReason,
    );
  }

  final bool screenAccepted;
  final bool committedEvidenceMatches;
  final bool experienceLensReady;
  final String? blockedReason;

  bool get canMountCommittedScreen =>
      screenAccepted && committedEvidenceMatches;
}

String? _screenAuthorityBlockedReason({
  required shell.InterfaceHostState? hostState,
  required bool screenAccepted,
  required bool committedEvidenceMatches,
}) {
  if (hostState == null) {
    return 'Waiting for Interface Host App screen authority.';
  }
  final appScreen = hostState.appScreen;
  if (!screenAccepted) {
    return _reasonFromParts(
      defaultReason: 'Waiting for accepted committed App screen.',
      status: appScreen?.status,
      reason: appScreen?.reason,
      error: appScreen?.error,
      blockers: appScreen?.blockers,
    );
  }
  if (!committedEvidenceMatches) {
    return 'Interface Host accepted a different App package revision or screen.';
  }
  return null;
}

bool _uuidMatches(UuidValue? actual, String expected) {
  return actual?.uuid.toLowerCase() == expected.trim().toLowerCase();
}

String _reasonFromParts({
  required String defaultReason,
  String? status,
  String? reason,
  String? error,
  List<String>? blockers,
}) {
  final details = <String>[
    if (status != null && status.trim().isNotEmpty) 'status=$status',
    if (reason != null && reason.trim().isNotEmpty) reason,
    if (error != null && error.trim().isNotEmpty) error,
    if (blockers != null && blockers.isNotEmpty) blockers.join(', '),
  ];
  if (details.isEmpty) {
    return defaultReason;
  }
  return '$defaultReason ${details.join(' ')}';
}

@immutable
class AwareAppCommittedScreen {
  const AwareAppCommittedScreen({
    required this.appConfigScreenConfigId,
    required this.screenKey,
    required this.projectionExperienceId,
    required this.projectionExperienceLayoutGraphBindingId,
  });

  final String appConfigScreenConfigId;
  final String screenKey;
  final String projectionExperienceId;
  final String projectionExperienceLayoutGraphBindingId;

  Map<String, dynamic> toEvidence() {
    return <String, dynamic>{
      'app_config_screen_config_id': appConfigScreenConfigId,
      'screen_key': screenKey,
      'projection_experience_id': projectionExperienceId,
      'projection_experience_layout_graph_binding_id':
          projectionExperienceLayoutGraphBindingId,
    };
  }
}

@immutable
class AwareAppLaunchManifest {
  const AwareAppLaunchManifest({
    required this.appPackage,
    required this.defaultScreenKey,
    required this.composition,
    required this.catalog,
    this.committedScreens = const <AwareAppCommittedScreen>[],
  });

  final AwareAppPackageEvidence appPackage;
  final String defaultScreenKey;
  final AwareAppComposition composition;
  final AwareAppRuntimeCatalog catalog;
  final List<AwareAppCommittedScreen> committedScreens;

  AwareAppCommittedScreen? committedScreenForKey(String screenKey) {
    final normalized = _normalizedOrNull(screenKey);
    if (normalized == null) {
      return null;
    }
    for (final screen in committedScreens) {
      if (_normalizedOrNull(screen.screenKey) == normalized) {
        return screen;
      }
    }
    return null;
  }

  List<String> validate() {
    final errors = <String>[];
    if (appPackage.packageName.trim().isEmpty) {
      errors.add('App package name must be non-empty');
    }
    _validateUuid(
      errors,
      label: 'App package id',
      value: appPackage.appPackageId,
    );
    _validateUuid(
      errors,
      label: 'App package branch id',
      value: appPackage.branchId,
    );
    _validateUuid(
      errors,
      label: 'App package object instance graph commit id',
      value: appPackage.objectInstanceGraphCommitId,
    );
    if (committedScreens.isEmpty) {
      errors.add('at least one committed App screen is required');
    }
    final screenKeys = <String>{};
    for (final screen in committedScreens) {
      final screenKey = _normalizedOrNull(screen.screenKey);
      if (screenKey == null) {
        errors.add('committed App screen key must be non-empty');
      } else if (!screenKeys.add(screenKey)) {
        errors.add('duplicate committed App screen key `${screen.screenKey}`');
      }
      _validateUuid(
        errors,
        label: 'App screen `${screen.screenKey}` config id',
        value: screen.appConfigScreenConfigId,
      );
      _validateUuid(
        errors,
        label: 'App screen `${screen.screenKey}` ProjectionExperience id',
        value: screen.projectionExperienceId,
      );
      _validateUuid(
        errors,
        label: 'App screen `${screen.screenKey}` layout graph binding id',
        value: screen.projectionExperienceLayoutGraphBindingId,
      );
    }
    final normalizedDefaultScreen = _normalizedOrNull(defaultScreenKey);
    if (normalizedDefaultScreen == null) {
      errors.add('default committed App screen key must be non-empty');
    } else if (!screenKeys.contains(normalizedDefaultScreen)) {
      errors.add(
        'default committed App screen `$defaultScreenKey` is not declared',
      );
    }
    final policyDefaultScreen = _normalizedOrNull(
      composition.controlPolicy.defaultScreenKey,
    );
    if (policyDefaultScreen == null ||
        !screenKeys.contains(policyDefaultScreen)) {
      errors.add('control policy default screen is not committed');
    }
    final admittedScreen = _normalizedOrNull(
      composition.controlPolicy.admittedScreenKey ?? '',
    );
    if (admittedScreen != null && !screenKeys.contains(admittedScreen)) {
      errors.add('control policy admitted screen is not committed');
    }
    if (catalog.registrations.isEmpty) {
      errors.add('at least one Interface package runtime is required');
    }
    final interfacePackageNames = <String>{};
    for (final registration in catalog.registrations) {
      final packageName = _normalizedOrNull(registration.interfacePackageName);
      if (packageName == null) {
        errors.add('Interface package runtime name must be non-empty');
      } else if (!interfacePackageNames.add(packageName)) {
        errors.add(
          'duplicate Interface package runtime '
          '`${registration.interfacePackageName}`',
        );
      }
    }
    return errors;
  }
}

@immutable
class AwareAppSectionPolicy {
  const AwareAppSectionPolicy({required this.layouts});

  const AwareAppSectionPolicy.empty() : layouts = const {};

  final Map<String, List<AwareAppSectionSpec>> layouts;

  List<AwareAppSectionSpec>? specsForLayout(String layoutKey) {
    return layouts[layoutKey];
  }
}

@immutable
class AwareAppSectionSpec {
  const AwareAppSectionSpec({
    required this.sectionKey,
    required this.region,
    required this.order,
    this.title,
    this.flex = 1.0,
    this.isVisible = true,
  });

  final String sectionKey;
  final WindowFullscreenSectionRegion region;
  final int order;
  final String? title;
  final double flex;
  final bool isVisible;

  shell.InterfaceShellSection toShellSection() {
    return shell.InterfaceShellSection(
      sectionKey: sectionKey,
      region: region,
      order: order,
      title: title,
      flex: flex,
      isVisible: isVisible,
    );
  }
}

String? _normalizedOrNull(String value) {
  final normalized = value.trim().toLowerCase();
  if (normalized.isEmpty) {
    return null;
  }
  return normalized;
}

void _validateUuid(
  List<String> errors, {
  required String label,
  required String value,
}) {
  try {
    UuidValue.fromString(value.trim());
  } on FormatException {
    errors.add('$label must be a UUID');
  }
}
