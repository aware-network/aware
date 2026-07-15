import 'pane_key.dart';
import 'pane_world_hint.dart';

/// Capability keys are intentionally opaque strings so hosts can define their
/// own vocabulary without coupling the package to a concrete enum.
typedef PaneCapabilityKey = String;

/// Describes what a pane can do and what it expects from the environment.
class PaneCapabilities {
  const PaneCapabilities({
    this.emits = const <PaneCapabilityKey>{},
    this.listens = const <PaneCapabilityKey>{},
    this.provides = const <PaneCapabilityKey>{},
    this.requires = const <PaneCapabilityKey>{},
    this.layout = const PaneLayoutPreferences(),
    this.framePolicy = PaneFramePolicy.embedded,
    this.allowedOverlays = const <PaneKey>{},
    this.chrome = const PaneChromeCapabilities(),
    this.worldHint,
  });

  /// Logical capabilities / events emitted by the pane.
  final Set<PaneCapabilityKey> emits;

  /// Capabilities / events the pane listens to.
  final Set<PaneCapabilityKey> listens;

  /// Capabilities the pane provides to collaborating panes.
  final Set<PaneCapabilityKey> provides;

  /// Capabilities the pane expects to be present in the host.
  final Set<PaneCapabilityKey> requires;

  /// Layout preferences to help window hosts size and arrange panes.
  final PaneLayoutPreferences layout;

  /// How the pane expects to be hosted (embedded vs overlay).
  final PaneFramePolicy framePolicy;

  /// Which panes can overlay on top of this one without conflicts.
  final Set<PaneKey> allowedOverlays;

  /// Header/overlay rendering capabilities advertised by the pane.
  final PaneChromeCapabilities chrome;

  /// Optional hints for the host-owned window “world” (background/lighting).
  final PaneWorldHint? worldHint;

  /// Soft compatibility check against another pane’s requirements.
  bool isCompatibleWith(PaneCapabilities other) {
    final weProvide = provides.containsAll(other.requires);
    final theyProvide = other.provides.containsAll(requires);
    return weProvide && theyProvide;
  }
}

/// Declarative capabilities related to window chrome.
class PaneChromeCapabilities {
  const PaneChromeCapabilities({
    this.providesWindowHeader = false,
    this.providesOverlayControls = false,
  });

  /// Pane renders its own header (window should suppress default header).
  final bool providesWindowHeader;

  /// Pane integrates with window overlays directly.
  final bool providesOverlayControls;
}

/// Layout preferences for panes.
class PaneLayoutPreferences {
  const PaneLayoutPreferences({
    this.minWidth = 200,
    this.maxWidth = double.infinity,
    this.preferredWidth = 400,
    this.minHeight = 100,
    this.maxHeight = double.infinity,
    this.preferredHeight = double.infinity,
    this.showHeader = true,
    this.collapsible = true,
    this.resizable = true,
    this.containerHeaderPolicy = PaneContainerHeaderPolicy.outer,
  });

  final double minWidth;
  final double maxWidth;
  final double preferredWidth;
  final double minHeight;
  final double maxHeight;
  final double preferredHeight;
  final bool showHeader;
  final bool collapsible;
  final bool resizable;
  final PaneContainerHeaderPolicy containerHeaderPolicy;
}

/// Policy describing who renders the header for the pane.
enum PaneContainerHeaderPolicy { none, outer, inner }

/// Hosting expectation (embedded within window vs overlay).
enum PaneFramePolicy { standalone, embedded, overlayCapable }
