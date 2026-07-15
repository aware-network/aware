# Aware Network

`aware_network` is the above-kernel workspace for live network dynamics.

It depends on `aware_kernel` for Code/Meta/Ontology foundations and owns the
network-facing communication, API, SDK, service, environment, identity,
attention, and experience layers as they are moved out of root.

This first checkpoint is intentionally minimal:

- workspace-root `libs/comms`
- module-owned API client raw code
- module-owned SDK core raw code

Network ontology, Environment, Identity, Attention, Service, and Experience
packages move in later passes.
