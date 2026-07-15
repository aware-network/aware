# Aware Control Interface

`aware_control` is the canonical bootstrap Interface package for the product
rail:

`aware-sdk -> CLI/Textual renderer -> Interface API -> mounted pane action -> host capability -> service API`.

The package mounts only the global Control panes required to enter the network:
Identity admission, Hub package discovery, and Network territory discovery.
Hub and Network actions stay behind mounted pane endpoint declarations;
renderers should not call those services directly.

This package is workspace agnostic. Product workspace composition belongs in
the workspace package tree; Aware Control must not link, select, or derive a
workspace Interface package or workspace primary experience.

Aware Control owns its shell topology through
`attentions/aware_control_shell/aware.attention.toml`. It must not depend on
the Workspace-owned `aware_workspace_shell` attention package.

Aware Control resolves reusable content render components through
`interfaces/render_components/aware_content_render_components/aware.render_component.toml`;
it must not depend on repo-root `render_components/*` packages.

## Pane Ownership Inventory

Aware Control composes pane packages owned by their domain modules. Root
`panes/*` packages are migration leftovers and must move one at a time.

| Pane | Package | Owner | Canonical target | Status |
| --- | --- | --- | --- | --- |
| `identity_admission` | `aware-identity-admission-pane` | `aware_network/modules/identity` | `workspaces/aware_network/modules/identity/interfaces/panes/identity_admission` | moved |
| `hub_package_selector` | `aware-hub-package-selector-pane` | `aware_network/modules/hub` | `workspaces/aware_network/modules/hub/interfaces/panes/hub_package_selector` | moved |
| `network_territory` | `aware-network-territory-pane` | `aware_network/modules/network` | `workspaces/aware_network/modules/network/interfaces/panes/network_territory` | moved |

Adjacent bootstrap panes discovered from the root `panes/` rail are not
owned by Aware Control:

| Pane | Owner | Canonical target | Status |
| --- | --- | --- | --- |
| `interface_admission` | `aware_network/modules/interface` | `workspaces/aware_network/modules/interface/interfaces/panes/interface_admission` | moved |
| `interface_mount_status` | `aware_network/modules/interface` | `workspaces/aware_network/modules/interface/interfaces/panes/interface_mount_status` | moved |
| `node_session_status` | `aware_network/modules/node` | `workspaces/aware_network/modules/node/interfaces/panes/node_session_status` | moved |
| `terminal` | `aware_agent/modules/agent` | `workspaces/aware_agent/modules/agent/panes/terminal` | root package pending move |
