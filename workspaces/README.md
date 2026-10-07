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

The original relocation preserved the then-accepted runtime, SDK, provider, CLI
and legal bytes. Later owner adoption is separately versioned and evidenced.
The original [Goal capsule manifest](../protocols/publication/goal-source-capsule/manifest.json)
retains its historical archive coordinates; its `source_path` values now point
directly into this tree. Three build inputs are mapped into `consumer_build` by
the source inventory. The attached capsule/archive itself is unchanged.
The [Issue source dispositions](../protocols/agent/source-provenance.json) retain
their original pinned owner coordinates and curated-facade qualifications.
Package README provenance links have been corrected for this layout only.

Install using [the pinned installer](../protocols/agent/install.py), not an
editable workspace or `PYTHONPATH`. The selected agent preview is **0.1.0a6**, with
22 reachable packages and agent contract **1.2.1**; see its
[publication record](../protocols/publication/A6-PUBLICATION.md).
The earlier [a4 adoption proof](../protocols/agent/REPOSITORY-A4-VERIFICATION.md)
is historical evidence for the shared publication-owner repair, not the current
client selection. Immutable earlier artifacts remain unchanged.
The Repository SDK still owns preparation only: full publication-SDK unification
is not claimed. Goal remains a separate qualified-input read-only preview.

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

## Versioned SPEC preview source

The [separate neutral snapshot](previews/specification-setup-read-v1/README.md)
keeps exact reviewed SPEC suppliers isolated from differing a6 inputs. Its presence
is not an agent-client upgrade, a new operation owner or a build acceptance.

## Retained admit-runtime SPEC source

The [versioned neutral snapshot](previews/specification-admit-runtime-v1/README.md)
preserves the exact successor inputs without replacing a6 or predecessor source.
The [delivery record](../protocols/specification/previews/admit-runtime-v1/PUBLICATION.md)
retains separate installations and accepted source/notice boundaries. The
[historical local selection](../protocols/specification/previews/admit-runtime-v1/SELECTION.md)
remains its own checkpoint. This is not an agent/bootstrap upgrade or a new
operation owner.

## Selected Git SPEC CLI022 source

The [separate versioned snapshot](previews/specification-cli022-reader-v1/README.md)
retains the exact reviewed reader sources for the selected Git preview.
See its [delivery record](../protocols/specification/previews/cli022-reader-v1/PUBLICATION.md)
and [historical selection](../protocols/specification/previews/cli022-reader-v1/SELECTION.md).
Independent local selection review is accepted. a6 and older
snapshots stay intact; no new operational rail or editable installation is admitted.

## Unselected SPEC CLI041 neutral sources

The [versioned snapshot](previews/specification-cli041-draft-v1/README.md)
retains the exact reviewed draft-composition source without replacing existing
source snapshots, selected installations or semantic owners.
