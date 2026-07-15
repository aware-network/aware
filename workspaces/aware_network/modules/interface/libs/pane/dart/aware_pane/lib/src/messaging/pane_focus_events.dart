import '../messaging/pane_event.dart';

class PaneFocusedEvent extends PaneEvent {
  PaneFocusedEvent({
    required this.windowId,
    required this.sectionId,
    required this.paneId,
    super.metadata,
  });

  final String windowId;
  final String sectionId;
  final String paneId;

  @override
  String get source => 'window_focus';

  @override
  Map<String, dynamic> toJson() => {
    'windowId': windowId,
    'sectionId': sectionId,
    'paneId': paneId,
  };
}

class PaneBlurredEvent extends PaneEvent {
  PaneBlurredEvent({
    required this.windowId,
    required this.sectionId,
    required this.paneId,
    super.metadata,
  });

  final String windowId;
  final String sectionId;
  final String paneId;

  @override
  String get source => 'window_focus';

  @override
  Map<String, dynamic> toJson() => {
    'windowId': windowId,
    'sectionId': sectionId,
    'paneId': paneId,
  };
}

class PaneFocusSuspendedEvent extends PaneEvent {
  PaneFocusSuspendedEvent({
    required this.windowId,
    this.sectionId,
    this.paneId,
    required this.overlayId,
    super.metadata,
  });

  final String windowId;
  final String overlayId;
  final String? sectionId;
  final String? paneId;

  @override
  String get source => 'window_focus';

  @override
  Map<String, dynamic> toJson() => {
    'windowId': windowId,
    'sectionId': sectionId,
    'paneId': paneId,
    'overlayId': overlayId,
  };
}

class PaneFocusResumedEvent extends PaneEvent {
  PaneFocusResumedEvent({
    required this.windowId,
    this.sectionId,
    this.paneId,
    this.overlayId,
    super.metadata,
  });

  final String windowId;
  final String? sectionId;
  final String? paneId;
  final String? overlayId;

  @override
  String get source => 'window_focus';

  @override
  Map<String, dynamic> toJson() => {
    'windowId': windowId,
    'sectionId': sectionId,
    'paneId': paneId,
    'overlayId': overlayId,
  };
}
