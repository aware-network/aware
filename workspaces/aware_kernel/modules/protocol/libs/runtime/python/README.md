# aware-protocol-runtime

Dependency-free canonical values for protocol identity, target selection,
record profile/role bindings, bootstrap references, and admission outcomes,
plus the narrow original bootstrap lifecycle.

This package is representation-neutral. It does not parse
`aware.protocol.toml`, normalize paths, read templates, inspect a filesystem,
select an SDK implementation, discover a service, or report installation
capabilities. Filesystem and later Service/API adapters lower
their source representations into these values while retaining
representation-specific locations in the adapter boundary.

Bootstrap values carry explicit string coordinates requested by the caller;
they are not filesystem handles or source authority. The SDK exposes these same
original values and strict codecs. The lifecycle retains execution/process
correlation, opaque plans and once-only admissions; physical validation and
effects remain with the explicitly selected FS owner. Genuine handles cannot
be reconstructed from decoded observations. Neither cleanup nor a refusal
restores spent authority.

Runtime **0.1.1** supplies the new module; SDK and FS require
`>=0.1.1,<0.2.0`, so an older 0.1.0 wheel cannot satisfy this composition.
Dependencies remain empty. This source composition adds no Service, Workspace,
Issue or FileSystem package dependency to the runtime. It does not qualify
continuous confinement, every-write detection or an installed initializer.
