import 'package:flutter/foundation.dart';

import 'pane_manifest_runtime.dart';

@immutable
class PaneSelectionContext {
  const PaneSelectionContext({this.descriptor, this.manifest});

  final Object? descriptor;
  final PaneManifestBundle<dynamic>? manifest;

  T? manifestPayload<T>() => manifest?.payload as T?;

  String get contextKey => manifest?.contextKey ?? '';

  PaneSelectionContext copyWith({
    Object? descriptor,
    PaneManifestBundle<dynamic>? manifest,
  }) {
    return PaneSelectionContext(
      descriptor: descriptor ?? this.descriptor,
      manifest: manifest ?? this.manifest,
    );
  }
}
