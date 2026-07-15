import 'package:aware_comms/service/duplex/protocol/models.dart';

abstract class DuplexFrameClient {
  Future<void> sendFrame(DuplexMessageFrame frame);

  Future<DuplexMessageFrame> readFrame({
    Duration timeout = const Duration(seconds: 5),
  });

  Future<DuplexMessageFrame> sendAndReceive(
    DuplexMessageFrame frame, {
    Duration timeout = const Duration(seconds: 5),
  });

  Future<void> close();
}
