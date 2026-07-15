# aware-comms

Shared communications transport and protocol models for AWARE clients and
services.

This package is moving toward a transport-neutral duplex substrate. Websocket
remains a concrete adapter, while the shared duplex protocol becomes the
canonical owner for request/response/ack/error/notification framing so future
IPC and service-host flows can reuse the same contract.

## Features (current / planned)

- Pydantic models for `NetworkOperation`, `NetworkRequest`, `NetworkResponse`,
  and FunctionCall payloads.
- Transport-neutral duplex message frames and request/response correlation
  helpers.
- Websocket client/server base classes as one duplex transport adapter.
- Local IPC endpoint/codec helpers plus process stdio and Python Unix-socket
  transports.
- Configurable registry for mapping application endpoints.
- Minimal logging hooks and retry helpers suitable for public SDKs.

## Status

Early extraction in progress. APIs are unstable until version `1.0.0`.
