export 'package:aware_pane/aware_pane.dart' show PaneKey;

import 'package:aware_pane/aware_pane.dart' show PaneKey;

const PaneKey kPaneKeyGeneric = 'generic';

extension PaneKeyExtensions on PaneKey {
  String get name => this;

  String get displayName {
    if (isEmpty) return 'Pane';
    final normalized = replaceAll(RegExp(r'[_-]+'), ' ');
    final withSpaces = normalized.replaceAll(
      RegExp(r'([a-z])([A-Z])'),
      r'$1 $2',
    );
    return withSpaces
        .split(' ')
        .where((token) => token.isNotEmpty)
        .map((token) => token[0].toUpperCase() + token.substring(1))
        .join(' ');
  }
}
