# aware-comms (Dart)

Shared communications transport and protocol helpers for AWARE clients.
This package mirrors the Python `workspaces/aware_network/libs/comms` direction: a transport-neutral
duplex protocol surface first, with websocket as one concrete adapter and IPC
reserved for later service-host/local-runtime use.

## Status

Early extraction in progress. APIs are unstable until version `1.0.0`.

## Current functionality

- Transport-neutral duplex frame models for request/response/ack/error/
  notification semantics.
- Generic duplex JSON request/stream client over the shared frame contract.
- Local IPC endpoint/codec helpers plus stdio/process IPC transport.
- WebSocket messenger (`NetworkMessenger`) as a concrete duplex transport with
  request/response correlation.
- `NullWebSocketChannel` for offline/testing usage.
- Compatibility `WsMessageFrame` models layered over the shared duplex
  protocol.
