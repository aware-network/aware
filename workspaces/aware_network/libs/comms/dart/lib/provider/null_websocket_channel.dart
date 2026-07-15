import 'dart:async';

import 'package:async/async.dart';
import 'package:logging/logging.dart';
import 'package:stream_channel/stream_channel.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class NullWebSocketSink extends DelegatingStreamSink<dynamic>
    implements WebSocketSink {
  NullWebSocketSink(StreamSink<dynamic> inner, this._label, this._logger)
      : super(inner);

  final String _label;
  final Logger _logger;

  void _log(String message) {
    _logger.finer('[$_label] $message');
  }

  @override
  void add(event) {
    _log('Dropping event: $event');
    super.add(event);
  }

  @override
  void addError(Object error, [StackTrace? stackTrace]) {
    _log('Dropping error: $error');
    super.addError(error, stackTrace);
  }

  @override
  Future close([int? closeCode, String? closeReason]) {
    _log('Closing (code=$closeCode reason=$closeReason)');
    return super.close();
  }
}

class NullWebSocketChannel extends StreamChannelMixin<dynamic>
    implements WebSocketChannel {
  NullWebSocketChannel({String label = 'stub-channel'})
      : _label = label,
        _incomingController = StreamController<dynamic>.broadcast(),
        _outgoingController = StreamController<dynamic>() {
    _outgoingController.stream.listen(
      (event) => _logger.finer('[$_label] Dropping event: $event'),
      onError: (error, stackTrace) =>
          _logger.finer('[$_label] Dropping error: $error'),
      onDone: () {
        if (!_incomingController.isClosed) {
          _incomingController.close();
        }
      },
    );
  }

  final Logger _logger = Logger('NullWebSocketChannel');
  final String _label;
  final StreamController<dynamic> _incomingController;
  final StreamController<dynamic> _outgoingController;
  NullWebSocketSink? _sink;
  int? _closeCode;
  String? _closeReason;

  String get label => _label;

  @override
  Stream<dynamic> get stream => _incomingController.stream;

  @override
  WebSocketSink get sink =>
      _sink ??= NullWebSocketSink(_outgoingController.sink, _label, _logger);

  @override
  String? get protocol => null;

  @override
  int? get closeCode => _closeCode;

  @override
  String? get closeReason => _closeReason;

  @override
  Future<void> get ready => Future.value();

  Future close([int? closeCode, String? closeReason]) async {
    _closeCode = closeCode;
    _closeReason = closeReason;
    await sink.close(closeCode, closeReason);
    await _outgoingController.close();
    if (!_incomingController.isClosed) {
      await _incomingController.close();
    }
  }
}
