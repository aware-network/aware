import '../runtime/pane_capabilities.dart';
import '../runtime/pane_key.dart';

/// Data-only representation describing collaboration expectations for a pane.
class PaneAgreementData {
  const PaneAgreementData({
    required this.paneKey,
    required this.title,
    this.provides = const <PaneCapabilityKey>{},
    this.requires = const <PaneCapabilityKey>{},
    this.emitsEvents = const <Type>{},
    this.listensToEvents = const <Type>{},
    this.cannotCoexistWith = const <PaneKey>{},
    this.metadata = const <String, Object?>{},
  });

  final PaneKey paneKey;
  final String title;
  final Set<PaneCapabilityKey> provides;
  final Set<PaneCapabilityKey> requires;
  final Set<Type> emitsEvents;
  final Set<Type> listensToEvents;
  final Set<PaneKey> cannotCoexistWith;
  final Map<String, Object?> metadata;
}
