# aware-protocol-runtime

Dependency-free canonical values for protocol identity, target selection,
record profile/role bindings, bootstrap references, and admission outcomes.

This package is representation-neutral. It does not parse
`aware.protocol.toml`, carry filesystem roots or templates, inspect a
filesystem, select an SDK implementation, discover a service, or report
installation capabilities. Filesystem and later Service/API adapters lower
their source representations into these values while retaining
representation-specific locations in the adapter boundary.
