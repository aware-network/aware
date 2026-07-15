# Aware Economy Interface

`aware_economy` is the Economy-owned Interface package that mounts Economy
panes without changing the shared `aware_control` shell.

The first mounted pane is `wallet_capital`, backed by
`aware_economy.home.wallet_capital.v1`. Interface owns placement and runtime
mount truth; Economy owns the pane source and view-state contract.

`aware_control` composition is intentionally out of scope while the Interface
mount-default cleanup lane owns that package.
