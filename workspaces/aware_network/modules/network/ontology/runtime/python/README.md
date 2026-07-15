# Aware Network Node

Maintains the network node service that brokers websocket connections, network routing, and commit distribution.

## Persistence Backend

The node relies on the ORM persistence backend to store interface bindings, ACLs, and future commit state. It is controlled through the `AWARE_PERSISTENCE_BACKEND` environment variable:

| Value | Behaviour |
| ----- | --------- |
| `db`  | Use the configured `DATABASE_URL` (PostgreSQL) for persistence. |
| `fs`  | Persist JSON records under `.aware/runtime/orm/…`, matching the agent workflow. |

If `AWARE_PERSISTENCE_BACKEND` is not set:
- When `DATABASE_URL` is present, the node defaults to `db`.
- Otherwise the node automatically falls back to `fs`, writing state to the repository filesystem.

You can override the default explicitly:

```bash
# Run the node entirely from filesystem persistence
AWARE_PERSISTENCE_BACKEND=fs uv run python -m services.node.aware_node_service.app

# Force database mode when a Postgres connection is available
AWARE_PERSISTENCE_BACKEND=db uv run python -m services.node.aware_node_service.app
```

The filesystem layout mirrors ObjectConfig schemas. For example, interface bindings live under `.aware/runtime/orm/interface/interface_session_network_binding/<branch>/<binding_id>.json`.
