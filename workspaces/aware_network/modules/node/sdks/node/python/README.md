# aware-node-sdk

Python Node SDK facade over the generated `aware_node_service_api` client.

The SDK keeps the public boundary thin: it builds generated Node service API
request DTOs, calls Product A client methods, returns generated response/model
objects, and stores only optional client-local cache entries.

## Operator Package Run Surface

Node runtime preparation is SDK-owned for operator ergonomics. The long-term
shape is:

```text
CLI command
-> aware_node_sdk package-run operation
-> NodePackage / NodeConfig
-> NodeRunManifest
-> operator-run
```

The hand-written `aware-cli node ontology-local ...` command is transitional.
It should delegate to the SDK surface now and later be generated from SDK
operation metadata. Operators should not need to import Node service internals or
know whether package truth came from local `aware.node.toml` or a later
WorkspaceRevision artifact.

Current source producers:

- local source: `aware.node.toml -> NodePackage / NodeConfig`
- later revision source: `WorkspaceRevision -> NodePackage / NodeConfig`

Both producers must feed the same package-run SDK facade before launch.

The current local package-run implementation uses a lazy `aware-node-service`
backend while the package/config DTO contract is being promoted. Install
`aware-node-sdk[local]`, or run from the workspace, when preparing a local
`aware.node.toml` package run.

Remote no-revision deployment must use the same SDK package-run facade. The
current generated run directory is not relocatable because paths are absolute,
so the first remote proof regenerates the manifest on the remote host after the
source runtime is present there. See
`workspaces/aware_network/modules/node/services/node/docs/REMOTE_NO_REVISION_NODE_DEPLOYMENT.md`.
