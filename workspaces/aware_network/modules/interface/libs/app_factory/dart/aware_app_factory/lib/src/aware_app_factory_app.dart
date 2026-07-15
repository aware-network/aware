import 'package:aware_shell/aware_shell.dart' as shell;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import 'aware_app_manifest.dart';

class AwareAppFactoryRoot extends StatelessWidget {
  const AwareAppFactoryRoot({
    required this.manifest,
    super.key,
    this.providerOverrides = const <Override>[],
  });

  final AwareAppLaunchManifest manifest;
  final List<Override> providerOverrides;

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      overrides: <Override>[
        shell.interfacePackageRuntimeRegistryProvider.overrideWithValue(
          manifest.catalog.buildRuntimeRegistry(),
        ),
        ...providerOverrides,
      ],
      child: AwareAppFactoryApp(manifest: manifest),
    );
  }
}

class AwareAppFactoryApp extends ConsumerStatefulWidget {
  const AwareAppFactoryApp({
    required this.manifest,
    super.key,
  });

  final AwareAppLaunchManifest manifest;

  @override
  ConsumerState<AwareAppFactoryApp> createState() => _AwareAppFactoryAppState();
}

class _AwareAppFactoryAppState extends ConsumerState<AwareAppFactoryApp> {
  bool _defaultScreenEntryScheduled = false;
  String? _pendingScreenKey;
  String? _screenEntryFailureMessage;

  @override
  void didUpdateWidget(AwareAppFactoryApp oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.manifest != widget.manifest) {
      _defaultScreenEntryScheduled = false;
      _pendingScreenKey = null;
      _screenEntryFailureMessage = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final validationErrors = widget.manifest.validate();
    if (validationErrors.isNotEmpty) {
      return _AwareAppFactoryMaterialShell(
        manifest: widget.manifest,
        child: _AwareAppFactoryBlockedView(
          title: 'App manifest is blocked',
          messages: validationErrors,
        ),
      );
    }

    final hostStateValue = ref.watch(shell.interfaceHostStateProvider);
    final hostState = hostStateValue.valueOrNull;
    final activeScreen = _screenFromHostState(hostState);
    _maybeEnterDefaultScreen(hostState: hostState, activeScreen: activeScreen);
    final runtime = ref.watch(shell.currentInterfacePackageRuntimeProvider);
    final readiness = ref.watch(
      shell.currentInterfacePackageRuntimeReadinessProvider,
    );
    final header = _AwareAppFactoryHeader(
      manifest: widget.manifest,
      activeScreen: activeScreen,
      hostState: hostState,
      pendingScreenKey: _pendingScreenKey,
      failureMessage: _screenEntryFailureMessage,
    );
    final content = _buildBrowserContent(
      hostStateValue: hostStateValue,
      hostState: hostState,
      activeScreen: activeScreen,
      runtime: runtime,
      readiness: readiness,
      header: header,
    );
    return _AwareAppFactoryMaterialShell(
      manifest: widget.manifest,
      child: content,
    );
  }

  Widget _buildBrowserContent({
    required AsyncValue<shell.InterfaceHostState> hostStateValue,
    required shell.InterfaceHostState? hostState,
    required AwareAppCommittedScreen? activeScreen,
    required shell.InterfacePackageRuntime? runtime,
    required shell.InterfacePackageRuntimeReadiness readiness,
    required Widget header,
  }) {
    if (hostState == null) {
      return _AwareAppFactoryBrowserPendingView(
        header: header,
        title: hostStateValue.hasError
            ? 'Interface Host unavailable'
            : 'Connecting to Interface Host',
        message: hostStateValue.hasError
            ? hostStateValue.error.toString()
            : 'Waiting for the shared Interface namespace.',
        showProgress: !hostStateValue.hasError,
      );
    }
    if (activeScreen == null) {
      final defaultScreen = widget.manifest.committedScreenForKey(
        widget.manifest.defaultScreenKey,
      );
      final authority = defaultScreen == null
          ? null
          : AwareAppSessionAuthority.fromHostState(
              hostState,
              appPackage: widget.manifest.appPackage,
              screen: defaultScreen,
              failureMessage: _screenEntryFailureMessage,
            );
      return _AwareAppFactoryBrowserPendingView(
        header: header,
        title: 'App screen unavailable',
        message: authority?.blockedReason ??
            'Waiting for Interface Host to accept a committed App screen.',
        showProgress: _pendingScreenKey != null,
      );
    }
    if (readiness.blocksRuntimeShell) {
      return _AwareAppFactoryBrowserPendingView(
        header: header,
        title: readiness.title,
        message: <String>[readiness.message, ...readiness.issues].join(' '),
      );
    }
    return ProviderScope(
      overrides: <Override>[
        shell.interfacePaneActionDispatcherProvider.overrideWith(
          (ref) => _AwareAppPaneActionDispatcher(
            ref,
            onAfterCanonicalAction: _afterCanonicalRenderSpecAction,
          ),
        ),
      ],
      child: shell.InterfaceHostRuntimeShell(
        hostState: hostState,
        panePackageRegistry:
            runtime?.panePackageRegistry ?? PanePackageRegistry(),
        interfacePackageRuntime: runtime,
        header: header,
      ),
    );
  }

  Future<shell.InterfaceHostState?> _afterCanonicalRenderSpecAction(
    shell.PaneRenderActionInvocation invocation,
  ) async {
    final screen = _admittedScreen();
    if (!isAwareAppControlAdmissionAction(invocation, screen)) {
      return null;
    }
    return _requestScreenEntry(
      screen: screen!,
      reason: 'control_action:${invocation.actionKey}',
      evidence: awareAppScreenEntryEvidence(
        appPackage: widget.manifest.appPackage,
        screen: screen,
        invocation: invocation,
      ),
    );
  }

  void _maybeEnterDefaultScreen({
    required shell.InterfaceHostState? hostState,
    required AwareAppCommittedScreen? activeScreen,
  }) {
    if (hostState == null ||
        hostState.appScreen != null ||
        activeScreen != null ||
        _defaultScreenEntryScheduled) {
      return;
    }
    final screen = widget.manifest.committedScreenForKey(
      widget.manifest.defaultScreenKey,
    );
    if (screen == null) {
      return;
    }
    _defaultScreenEntryScheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      _requestScreenEntry(
        screen: screen,
        reason: 'aware_app_default_screen',
        evidence: <String, dynamic>{
          'source': 'aware_app_factory',
          'aware_app_package': widget.manifest.appPackage.toEvidence(),
          'aware_app_screen': screen.toEvidence(),
        },
      );
    });
  }

  AwareAppCommittedScreen? _admittedScreen() {
    final admittedScreenKey =
        widget.manifest.composition.controlPolicy.admittedScreenKey;
    if (admittedScreenKey == null) {
      return null;
    }
    return widget.manifest.committedScreenForKey(admittedScreenKey);
  }

  AwareAppCommittedScreen? _screenFromHostState(
    shell.InterfaceHostState? hostState,
  ) {
    for (final screen in widget.manifest.committedScreens) {
      final authority = AwareAppSessionAuthority.fromHostState(
        hostState,
        appPackage: widget.manifest.appPackage,
        screen: screen,
      );
      if (authority.canMountCommittedScreen) {
        return screen;
      }
    }
    return null;
  }

  Future<shell.InterfaceHostState> _requestScreenEntry({
    required AwareAppCommittedScreen screen,
    required String reason,
    required Map<String, dynamic> evidence,
  }) async {
    if (mounted) {
      setState(() {
        _pendingScreenKey = screen.screenKey;
        _screenEntryFailureMessage = null;
      });
    }
    try {
      final appPackage = widget.manifest.appPackage;
      final hostState = await ref
          .read(shell.interfaceHostStateProvider.notifier)
          .enterAppScreen(
            appPackageId: UuidValue.fromString(appPackage.appPackageId),
            appPackageBranchId: UuidValue.fromString(appPackage.branchId),
            appPackageObjectInstanceGraphCommitId: UuidValue.fromString(
              appPackage.objectInstanceGraphCommitId,
            ),
            appConfigScreenConfigId: UuidValue.fromString(
              screen.appConfigScreenConfigId,
            ),
            reason: reason,
            evidence: evidence,
          );
      final authority = AwareAppSessionAuthority.fromHostState(
        hostState,
        appPackage: appPackage,
        screen: screen,
      );
      if (!authority.canMountCommittedScreen) {
        throw StateError(
          authority.blockedReason ??
              'Interface Host did not accept committed App screen '
                  '`${screen.screenKey}`.',
        );
      }
      if (mounted) {
        setState(() {
          _pendingScreenKey = null;
        });
      }
      return hostState;
    } catch (error) {
      if (mounted) {
        setState(() {
          _pendingScreenKey = null;
          _screenEntryFailureMessage = error.toString();
        });
      }
      rethrow;
    }
  }
}

class _AwareAppPaneActionDispatcher
    extends shell.InterfacePaneActionDispatcher {
  // The shell dispatcher owns a private Ref field, so this subclass cannot use
  // a super parameter while preserving the canonical action implementation.
  // ignore: use_super_parameters
  _AwareAppPaneActionDispatcher(
    Ref ref, {
    required this.onAfterCanonicalAction,
  }) : super(ref);

  final Future<shell.InterfaceHostState?> Function(
    shell.PaneRenderActionInvocation invocation,
  ) onAfterCanonicalAction;

  @override
  Future<shell.InterfaceHostState> invokeRenderSpecAction(
    shell.PaneRenderActionInvocation invocation,
  ) async {
    final canonicalState = await super.invokeRenderSpecAction(invocation);
    return await onAfterCanonicalAction(invocation) ?? canonicalState;
  }
}

class _AwareAppFactoryMaterialShell extends StatelessWidget {
  const _AwareAppFactoryMaterialShell({
    required this.manifest,
    required this.child,
  });

  final AwareAppLaunchManifest manifest;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: manifest.composition.displayName,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Color(manifest.composition.seedColorValue),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF080A0F),
        useMaterial3: true,
      ),
      home: child,
    );
  }
}

class _AwareAppFactoryHeader extends StatelessWidget {
  const _AwareAppFactoryHeader({
    required this.manifest,
    required this.activeScreen,
    required this.hostState,
    required this.pendingScreenKey,
    required this.failureMessage,
  });

  final AwareAppLaunchManifest manifest;
  final AwareAppCommittedScreen? activeScreen;
  final shell.InterfaceHostState? hostState;
  final String? pendingScreenKey;
  final String? failureMessage;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final connected = hostState?.transport.available == true;
    final screenLabel = pendingScreenKey ?? activeScreen?.screenKey;
    final statusColor = failureMessage == null
        ? theme.colorScheme.onSurfaceVariant
        : theme.colorScheme.error;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withValues(alpha: 0.88),
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outlineVariant.withValues(alpha: 0.42),
          ),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  manifest.composition.displayName,
                  style: theme.textTheme.titleMedium,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Icon(
                connected ? Icons.cloud_done_outlined : Icons.cloud_off,
                size: 18,
                color: statusColor,
              ),
              if (screenLabel != null) ...[
                const SizedBox(width: 10),
                Text(
                  screenLabel,
                  style: theme.textTheme.labelLarge?.copyWith(
                    color: statusColor,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _AwareAppFactoryBrowserPendingView extends StatelessWidget {
  const _AwareAppFactoryBrowserPendingView({
    required this.header,
    required this.title,
    required this.message,
    this.showProgress = false,
  });

  final Widget header;
  final String title;
  final String message;
  final bool showProgress;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Column(
        children: [
          header,
          Expanded(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 520),
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (showProgress) ...[
                        const CircularProgressIndicator(),
                        const SizedBox(height: 20),
                      ],
                      Text(title, style: theme.textTheme.titleLarge),
                      const SizedBox(height: 8),
                      Text(
                        message,
                        textAlign: TextAlign.center,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AwareAppFactoryBlockedView extends StatelessWidget {
  const _AwareAppFactoryBlockedView({
    required this.title,
    required this.messages,
  });

  final String title;
  final List<String> messages;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: theme.textTheme.headlineSmall),
                const SizedBox(height: 12),
                for (final message in messages)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(
                      message,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
