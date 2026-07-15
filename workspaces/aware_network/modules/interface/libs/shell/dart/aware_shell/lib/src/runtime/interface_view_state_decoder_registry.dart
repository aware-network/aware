import 'package:aware_interface_service_api/aware_interface_service_api.dart';

typedef InterfaceViewStateDecoder = Object Function(Map<String, dynamic> json);

enum InterfaceViewStateDecodeStatus {
  decoded,
  missingMaterializedState,
  missingViewIdentity,
  missingDecoder,
  invalidPayload,
  typeMismatch,
}

class InterfaceViewStateDecodeResult<T extends Object> {
  const InterfaceViewStateDecodeResult({
    required this.status,
    this.value,
    this.materializedState,
    this.viewRef,
    this.viewKey,
    this.decoderKey,
    this.error,
  });

  final InterfaceViewStateDecodeStatus status;
  final T? value;
  final InterfaceMaterializedPaneState? materializedState;
  final String? viewRef;
  final String? viewKey;
  final String? decoderKey;
  final Object? error;

  bool get hasValue =>
      status == InterfaceViewStateDecodeStatus.decoded && value != null;
}

class InterfaceViewStateDecoderRegistry {
  const InterfaceViewStateDecoderRegistry.empty()
    : _decoders = const <String, InterfaceViewStateDecoder>{};

  InterfaceViewStateDecoderRegistry.fromDecoderMaps(
    Iterable<Map<String, InterfaceViewStateDecoder>> decoderMaps,
  ) : _decoders = _mergeDecoderMaps(decoderMaps);

  final Map<String, InterfaceViewStateDecoder> _decoders;

  bool get isEmpty => _decoders.isEmpty;

  bool hasDecoder({String? viewRef, String? viewKey}) {
    return _resolveDecoder(viewRef: viewRef, viewKey: viewKey) != null;
  }

  InterfaceViewStateDecodeResult<T> decodeMaterialized<T extends Object>({
    required InterfaceMaterializedPaneState? materializedState,
    String? viewRef,
    String? viewKey,
  }) {
    if (materializedState == null) {
      return InterfaceViewStateDecodeResult<T>(
        status: InterfaceViewStateDecodeStatus.missingMaterializedState,
        viewRef: _trimmedOrNull(viewRef),
        viewKey: _trimmedOrNull(viewKey),
      );
    }

    final resolvedViewRef =
        _trimmedOrNull(viewRef) ??
        _stringFromMap(materializedState.provenance, 'view_ref');
    final resolvedViewKey =
        _trimmedOrNull(viewKey) ??
        _stringFromMap(materializedState.provenance, 'projection_view_key');
    final decoder = _resolveDecoder(
      viewRef: resolvedViewRef,
      viewKey: resolvedViewKey,
    );
    if (decoder == null) {
      final missingStatus = resolvedViewRef == null && resolvedViewKey == null
          ? InterfaceViewStateDecodeStatus.missingViewIdentity
          : InterfaceViewStateDecodeStatus.missingDecoder;
      return InterfaceViewStateDecodeResult<T>(
        status: missingStatus,
        materializedState: materializedState,
        viewRef: resolvedViewRef,
        viewKey: resolvedViewKey,
      );
    }

    try {
      final decoded = decoder.decoder(
        Map<String, dynamic>.from(materializedState.state),
      );
      if (decoded is T) {
        return InterfaceViewStateDecodeResult<T>(
          status: InterfaceViewStateDecodeStatus.decoded,
          value: decoded,
          materializedState: materializedState,
          viewRef: resolvedViewRef,
          viewKey: resolvedViewKey,
          decoderKey: decoder.key,
        );
      }
      return InterfaceViewStateDecodeResult<T>(
        status: InterfaceViewStateDecodeStatus.typeMismatch,
        materializedState: materializedState,
        viewRef: resolvedViewRef,
        viewKey: resolvedViewKey,
        decoderKey: decoder.key,
        error:
            'Decoded view state type ${decoded.runtimeType} is not assignable to $T.',
      );
    } catch (error) {
      return InterfaceViewStateDecodeResult<T>(
        status: InterfaceViewStateDecodeStatus.invalidPayload,
        materializedState: materializedState,
        viewRef: resolvedViewRef,
        viewKey: resolvedViewKey,
        decoderKey: decoder.key,
        error: error,
      );
    }
  }

  _InterfaceViewStateDecoderEntry? _resolveDecoder({
    String? viewRef,
    String? viewKey,
  }) {
    final normalizedViewRef = _trimmedOrNull(viewRef);
    if (normalizedViewRef != null) {
      final decoder = _decoders[normalizedViewRef];
      if (decoder != null) {
        return _InterfaceViewStateDecoderEntry(
          key: normalizedViewRef,
          decoder: decoder,
        );
      }
    }
    final normalizedViewKey = _trimmedOrNull(viewKey);
    if (normalizedViewKey != null) {
      final decoder = _decoders[normalizedViewKey];
      if (decoder != null) {
        return _InterfaceViewStateDecoderEntry(
          key: normalizedViewKey,
          decoder: decoder,
        );
      }
    }
    return null;
  }

  static Map<String, InterfaceViewStateDecoder> _mergeDecoderMaps(
    Iterable<Map<String, InterfaceViewStateDecoder>> decoderMaps,
  ) {
    final merged = <String, InterfaceViewStateDecoder>{};
    for (final decoderMap in decoderMaps) {
      for (final entry in decoderMap.entries) {
        final key = _trimmedOrNull(entry.key);
        if (key == null || merged.containsKey(key)) {
          continue;
        }
        merged[key] = entry.value;
      }
    }
    return Map<String, InterfaceViewStateDecoder>.unmodifiable(merged);
  }
}

class _InterfaceViewStateDecoderEntry {
  const _InterfaceViewStateDecoderEntry({
    required this.key,
    required this.decoder,
  });

  final String key;
  final InterfaceViewStateDecoder decoder;
}

String? _stringFromMap(Map<String, dynamic> payload, String key) {
  final value = payload[key];
  if (value is! String) {
    return null;
  }
  return _trimmedOrNull(value);
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
