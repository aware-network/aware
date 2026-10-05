# Neutral consumer source workspaces

Only source required by the published filesystem products belongs here. This
is a curated consumer tree, not a restored Aware development checkout. No
`aware.repo.toml`, workspace publication manifests, generated APIs/DTOs,
ontology/ORM, services or Experience implementations are admitted.

| Workspace | Approved responsibility |
| --- | --- |
| `aware_kernel/modules/protocol` | Neutral Protocol contracts, SDK and filesystem admission adapter |
| `aware_coordination/modules/workflow` | Neutral Goal reader and Issue owners, SDKs, FS adapters and thin agent/Issue CLIs |
| `aware_workspace` | Neutral repository preparation SDK/FS adapter and scoped Git publication owner |
| `consumer_build/goal_fs` | Retained Goal consumer build spec and source-derived jsonschema packaging recipe/constraints |

The [exact source inventory](../protocols/publication/source-layout.json) maps
every admitted file from its prior public coordinate and records its bytes and
hash. Seven Goal/Protocol projects and nine agent/Issue/repository projects are
present. Those **16 source projects are not 16 new interfaces**: use only the
commands admitted by each [consumer profile](../protocols/agent/README.md).
Third-party wheels are inputs in the immutable distributions, not copied source
workspaces. Their source and notices remain pinned in the accompanying evidence.

`protocols/` owns operational profiles, versioned workflow/agent templates,
installation, evaluation schemas, distribution artifacts and provenance.
Packaged agent templates here are generated from `protocols/contracts/`; they
are not independently authored workflow rules. Domain code is not duplicated
under `protocols/`. Retained historical builders and nested source attachments
are evidence for old immutable artifacts, not a second active source rail.

## Source identity and installation

Relocation preserves the accepted runtime, SDK, provider, CLI and legal bytes.
The original [Goal capsule manifest](../protocols/publication/goal-source-capsule/manifest.json)
retains its historical archive coordinates; its `source_path` values now point
directly into this tree. Three build inputs are mapped into `consumer_build` by
the source inventory. The attached capsule/archive itself is unchanged.
The [Issue source dispositions](../protocols/agent/source-provenance.json) retain
their original pinned owner coordinates and curated-facade qualifications.
Package README provenance links have been corrected for this layout only.

Install using [the pinned installer](../protocols/agent/install.py), not an
editable workspace or `PYTHONPATH`. Current customer version is **0.1.0a3**;
its archive, wheels and 22-package dependency closure are unchanged by this
source reorganization. Goal remains a separate qualified-input read-only preview.

## Maintain and build

Use one exact-scope Issue through the installed tooling. Changes to package
contents/dependencies need a new reviewed candidate, affected installed proofs,
notices and disclosure review. A directory name does not admit new capabilities.
Adding any other source requires an explicit value/boundary review.

The active agent builder reads these public source projects by default:

```sh
python3.12 protocols/agent/build_bundle.py --registry-wheelhouse /absolute/pinned-registry-wheels
```

It refuses to overwrite the current immutable candidate. Update the authored
CLI version only inside a separately governed candidate Issue before building.
Build-backend acquisition and registry verification require their declared
build tools/network inputs; customer installation remains offline. This layout
cut does not claim an independently rebuilt or reproducible future candidate.
Refreshing the original six owner projections is a separate, explicit
`--refresh-owner-sources --source-repository <pinned-owner-repository>` operation,
never an automatic import of the internal checkout. Goal's pinned source/build
inputs remain inspectable; no new Goal writer or build acceptance is implied.
