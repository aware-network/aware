# aware-interface-sdk

Handwritten Interface SDK facade over the generated Interface service API.

Primary entrypoints:

- `InterfaceSdkClient`
- `InterfaceSurfaceSnapshot`
- `create_interface_attachment`
- `InterfaceAttachment`
- `get_sdk_operation_catalog`
- `dispatch_interface_sdk_operation`

## Public Boundary

- Wraps the generated `aware_interface_service_api` client as the canonical
  consumer boundary.
- Supports `aware-interface-sdk[local]` for source-local Interface Host
  development; that extra installs the Interface service host adapter so local
  consumers still enter through the generated Interface service API.
- Renders host surfaces as screens, panes, and pane API capability endpoints.
- Validates pane-scoped capability membership before invoking Interface API
  endpoints.
- Keeps `aware-sdk`, `apps/interface_textual`, and future renderers on the
  generated Interface service API surface.
- The default client facade does not import Interface service internals, Hub
  service internals, Workspace service internals, local graph gateways, runtime
  indexes, or full `aware-code`. The `[local]` bootstrap path may lazily import
  the service-owned local ServiceHost harness to start a source-local
  `aware-interface-service`.

The intended product path is:

```text
renderer -> aware-interface-sdk -> generated Interface service API
-> workspaces/aware_network/modules/interface/services/interface
-> pane capability endpoint -> owning API/service
```

Hub, Workspace, Node, Identity, Economy, and Attention workflows must enter via
mounted Interface panes and their API capability endpoints. The SDK may help
render and invoke those panes; it does not own domain truth.

## SDK Operation Catalog

`aware-interface-sdk` also publishes the first preview SDK operation catalog
provider for generic CLI/tooling renderers:

```text
aware_interface_sdk.operation_catalog:get_sdk_operation_catalog
```

The catalog is exposed through the `aware.sdk_operation_catalogs` entry point
group and currently declares read-only canaries:

- `interface_sdk.ping_interface_host`
- `interface_sdk.list_interface_namespaces`

The catalog is explicit operation metadata, not method reflection. Each
operation declares endpoint refs, schemas, read/write effect metadata, and a
handler ref. The canonical actor-facing package at
`workspaces/aware_network/modules/interface/sdks/aware` can render this as
`aware sdk ...` without depending on Interface panes for every raw terminal
operation.

## Interface Attachment Boundary

The SDK owns the concrete renderer-to-Interface attachment rail. Interface Host
code asks `aware-interface-sdk` to create an `InterfaceAttachment`; it does not
construct lower-level session stores, transport registrations, or boot runtime
ports directly.

Current responsibilities:

- resolve/create the canonical Interface id for the renderer namespace
- register the transport session against the Interface service boundary
- persist authenticated actor-to-Interface attachment when login succeeds
- bootstrap the Interface graph through the configured boot program
- provide the runtime port consumed by `workspaces/aware_network/modules/interface/ontology/runtime/python`

`libs/session` remains a private compatibility detail under this SDK while the
canonical Interface API/ontology rail is being completed. It is intentionally
not part of the SDK semantic package model; that model depends only on
`interface-service-api`. New service/runtime code should depend on
`InterfaceAttachment`, not on `AwareSession` wrappers.

## Host Startup Boundary

The local SDK startup rail starts or reuses a ServiceHost-backed
`aware-interface-service` and then admits the renderer namespace through the
generated Interface service API. `aware-interface-control` is compatibility
only and is not the SDK default local authority.

Product renderers such as `aware` / `aware-sdk` do not own daemon startup,
Kernel boot, Hub routing, or Workspace routing in the action path. They consume
this SDK, render the mounted Interface surface, and emit pane-scoped actions
such as `hub_package_selector` + `api:hub.code_package.search` to the Interface
host.

## Mock Host Contract Smoke

The SDK owns the direct client-contract smoke for the dev mock host. The mock
process itself lives in
`workspaces/aware_network/modules/interface/libs/interface_mock/python`, but the
SDK test treats it as a black-box Interface Host-compatible process and talks to
it through the local transport adapter.

Run the direct lock smoke:

```bash
uv run --project workspaces/aware_network/modules/interface/sdks/interface/python pytest -q \
  workspaces/aware_network/modules/interface/sdks/interface/python/tests/test_interface_sdk_mock_contract.py
```

The broader AX/product proof lives in
`integrations/aware-sdk-interface-agent-dogfood` and exercises the public
`aware-sdk` CLI against the same mock host contract.
