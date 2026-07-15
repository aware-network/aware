---
title: "Interface Session Binding Manager"
code_path: ../aware_network/communications/interface_session_binding_manager.py
test_path: ../tests/test_interface_session_binding_manager.py
code_sha: 90e4cb5a17b9692f943103846e2c59d01c3c90e8
last_validated: "2025-10-15T23:45:04Z"
---

# Interface Session Binding Manager

The binding manager keeps an **in-memory** registry that links an identity’s active interface websocket
connections to the current network node. It is a transport-scoped helper for fan-out routing and session
gating; it does **not** persist anything to the graph.

## Responsibilities

- **Session Binding Lifecycle** – create/refresh an in-memory binding when the node receives the canonical DTO
  `NetworkNodeOperationRequest.interface_session_register`; update `last_seen_at` when the node receives
  `NetworkNodeOperationRequest.interface_session_heartbeat`; remove the binding on transport disconnect.
- **In-Memory Lookup** – translate identities into active websocket connection IDs for fan-out.

## Public API

```python
from aware_network.communications.interface_session_binding_manager import InterfaceSessionBindingManager

manager = InterfaceSessionBindingManager.instance()
context = await manager.register_connection(connection_id, payload)
await manager.record_heartbeat(connection_id=connection_id)
await manager.disconnect(connection_id=connection_id)
```

## Test Coverage

`tests/test_interface_session_binding_manager.py` exercises registration, heartbeat, and disconnect flows with an
in-memory store, ensuring the manager updates binding contexts as expected.

The canonical DTO handshake itself is validated at the node/router layer (not here).
