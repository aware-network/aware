# Aware canonical filesystem source and notice review envelope

This internal review envelope carries an already tested shared installation,
its exact neutral source snapshot and applicable upstream notice inputs.
Public-content acceptance, instruction freeze, selection and delivery remain
separate. This is not a registry release or a unified `aware` command.

## Installation for technical review

Qualified target: Linux x86-64 with Python 3.12. Use a fresh separate environment;
do not overlay a6 or a historical SPEC installation. Verify outer SHA256SUMS,
then expand payload/aware-canonical-neutral-fs-internal-v1.tar.gz in a new private
directory. It expands into aware-canonical-neutral-fs-internal-v1. Its `internal`
name identifies a retained candidate, not an additional authority mode.
Verify the inner SHA256SUMS and invoke its shipped installer:

```bash
PYTHON_BIN=/usr/bin/python3.12 /bin/sh ./install.sh /absolute/fresh/environment
```

The target must be absent and its private parent must exist. The installer
refuses existing targets and selects the declared interpreter minor. Supported
family commands are aware-issue-cli, aware-protocol and aware-spec from this
same environment. Inspect their installed `--help`; do not substitute another
installation or regard a transitive entrypoint as an admitted interface.

Issue publication/closeout, governed SPEC setup and draft preview/apply/reading
are the accepted filesystem operations. They still require exact customer
repository, Issue, manifest, target and byte guards. Approval, approved
iterations, Goal writers, Service/API and Experience authority are unavailable.
Observed-state currentness is not every-write detection; cooperative descriptor
confinement is not continuous confinement. Preserve applied/unknown effects
and never automatically retry a known publication.

## Source and notices

`source/` is the canonical selected neutral snapshot, not Aware's whole
development checkout, a source-discovery inventory or a second runtime rail.
SOURCE-INDEX.json correlates every attached byte to committed source and the
unchanged wheels. The source-derived jsonschema recipe/constraints and exact
publisher source URL/hash are under build-inputs/jsonschema. This is source
transparency, not an independently reproducible-build claim. No public source
coordinate for this newly assembled envelope is claimed yet.

Keep LICENSE, NOTICE, all notices, upstream source archives and indexes with
the payload. Aware's Apache-2.0 policy does not replace upstream terms. The
original schema notice selects BSD-3-Clause while retaining the complete
upstream file, including the alternative AFL text, and the package MIT notice.
Pathspec's MPL-2.0 terms and corresponding source archive remain attached.

NOTICE-BINDINGS.json rebinds exact notice inputs to this payload. Inherited
indexes and the original new-dependency draft refer to their historical
candidate; those files remain exact evidence, not this envelope's authority.
The 18 rpds and 103 pydantic-core crate candidate accounts are conservative
coverage, not exact binary linkage. Cython 3.3.0 is correlated to msgpack's
generated header, not assigned to PyYAML. LibYAML 0.2.5 is precautionary input
from configurable upstream CI, not a publisher-toolchain attestation.

CONTENT-AUDIT.json reports all bounded scan findings without suppressing them.
No scan proves exhaustive secret detection, authorship or legal sufficiency.
This envelope needs independent byte/content review before any public layout,
consumer freeze, transfer or release.
