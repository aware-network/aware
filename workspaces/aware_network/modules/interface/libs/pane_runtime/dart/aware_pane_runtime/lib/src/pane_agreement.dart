import 'pane_kind.dart';

typedef PaneId = String;

enum PaneCapability {
  processSelection,
  threadSelection,
  threadManagement,
  taskCreation,
  fileNavigation,
  codeEditing,
  gitOperations,
  contextBroadcast,
  taskManagement,
  projectManagement,
  agentManagement,
  identityManagement,
  agentCreation,
  conversation,
  conversationAccess,
  sessionManagement,
  messageComposition,
  threadVisualization,
  repositoryAccess,
  configurationAccess,
  analyticsAccess,
  dataVisualization,
  contentEditing,
  networkMessaging,
  authenticationServices,
  oigSynchronization,
}

class PaneAgreement {
  const PaneAgreement({
    required this.paneId,
    required this.title,
    this.paneKind,
    this.provides = const {},
    this.requires = const {},
    this.emitsEvents = const {},
    this.listensToEvents = const {},
    this.cannotCoexistWith = const {},
  });

  final PaneId paneId;
  final String title;
  final PaneKey? paneKind;
  final Set<PaneCapability> provides;
  final Set<PaneCapability> requires;
  final Set<Type> emitsEvents;
  final Set<Type> listensToEvents;
  final Set<String> cannotCoexistWith;
}
