import 'package:flutter/widgets.dart';

/// Who owns the primary pane header row.
///
/// Canonical:
/// - When [PaneChromeHeaderPolicy.sharedChrome], panes should not render an
///   embedded title/header row; they should contribute chrome context instead.
enum PaneChromeHeaderPolicy { paneOwned, sharedChrome }

/// Host-provided chrome scope for panes.
///
/// This avoids module panes importing the app package to determine if shared
/// chrome is active and which mount section they are rendered within.
class PaneChromeScope extends InheritedWidget {
  const PaneChromeScope({
    super.key,
    required this.windowId,
    required this.sectionId,
    this.headerPolicy = PaneChromeHeaderPolicy.sharedChrome,
    required super.child,
  });

  final String windowId;
  final String sectionId;
  final PaneChromeHeaderPolicy headerPolicy;

  bool get sharedChromeEnabled =>
      headerPolicy == PaneChromeHeaderPolicy.sharedChrome;

  static PaneChromeScope? maybeOf(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<PaneChromeScope>();
  }

  static PaneChromeScope of(BuildContext context) {
    final scope = maybeOf(context);
    assert(scope != null, 'PaneChromeScope is missing above this widget.');
    return scope!;
  }

  @override
  bool updateShouldNotify(PaneChromeScope oldWidget) {
    return windowId != oldWidget.windowId ||
        sectionId != oldWidget.sectionId ||
        headerPolicy != oldWidget.headerPolicy;
  }
}
