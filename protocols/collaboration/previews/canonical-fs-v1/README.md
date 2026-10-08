# Canonical filesystem collaboration — unselected layout

This is a review-only instruction proposal, not selected or publicly delivered.
It prepares one shared installation for Issue/repository operations, governed
SPEC setup, draft preview/apply and reading. Existing a6, CLI022 and CLI041
selections remain unchanged. Instructions remain draft; no version is allocated.

## Install once into a fresh environment

Prerequisites: Linux x86-64, actual Python 3.12 and Git. From the prepared
checkout, choose the actual interpreter explicitly. The temporary parent below
is private; the environment must not already exist.

```sh
canonical_parent="$(mktemp -d /tmp/aware-canonical.XXXXXXXX)"
canonical_env="$canonical_parent/env"
/usr/bin/python3.12 protocols/collaboration/previews/canonical-fs-v1/install.py \
  --python-executable /usr/bin/python3.12 --venv "$canonical_env"
ISSUE="$canonical_env/bin/aware-issue-cli"
PROTOCOL="$canonical_env/bin/aware-protocol"
SPEC="$canonical_env/bin/aware-spec"
"$ISSUE" --help
"$PROTOCOL" --help
"$SPEC" --help
```

The wrapper verifies the exact envelope and payload, retains source/notices,
and invokes the unchanged shipped offline installer. Existing targets, symlinks
and missing/symlink parents refuse; parent permissions remain unchanged.
After acquisition, installation requires neither networking nor Aware's checkout.
Never overlay a6 or a previous preview. Failed installation may leave partial
effects: preserve its evidence. consumer-lock.json is accounting, not a pip
requirements file. No editable imports, source launcher or automatic upgrade.

**One installation, three family commands—not yet a unified aware entrance.**
There is no aware init, aware spec or aware-issue-cli open here. This candidate
requires an already prepared Git repository and admitted aware.protocol.toml.
It does not supply a supported new-repository/profile bootstrap or import route.
Do not hand-author authority records to conceal that gap. The independently
selected [a6 entrance](../../../agent/quickstart.md) remains available separately;
cross-candidate bootstrap equivalence is not established by this layout.

For prepared inputs, follow [the family workflow](WORKFLOW.md). A proposed
[agent template](AGENTS.template.md) records these limits; it is not installed
into customer repositories and must not overwrite an existing AGENTS.md.

## What is supported

Issue snapshots, progress, scope, publication and closeout use the original
Issue SDK/provider and repository owner. SPEC setup prepares only explicitly
admitted directories and the manifest binding. Governed draft creation validates
staged semantics through SPEC's parser, then fresh observation reads the result.
Publication and Issue closeout are separate from draft creation.

No SPEC approval/import, approved-iteration authoring, durable iteration-to-Issue
binding, Goal writer, dispatch, Service/API, ontology/ORM or Experience authority.
Currentness checks observed state; every-write detection and continuous
confinement remain unsupported. Actor strings are not authenticated action
issuance. Known publication must never be automatically retried.

## Composition, sources and notices

Workspace's authored portable_protocols profile is the sole software selector.
This layout maps its accepted envelope, without another package registry,
dependency solver, pruning step or operation engine. aware.protocol.toml selects
customer records/authority, not distribution packages. delivery.json and inner
locks are generated evidence—not agent-authored selection files.

- [Unchanged envelope](distribution/canonical-neutral-source-notice-review-v1.tar.gz), SHA-256 `d135c339b7c14d28d2df1ed7c4335fad71e3d5e163c3ede70f3cef692c679f75`.
- Accepted payload SHA-256 `6225a71ca27450170ec3b1d55336191d52fc5346c7739fff73141febb4877fb1`: 31 packages, including 18 Aware packages.
- [Delivery map](delivery.json): all 853 envelope members and their public paths.
- [Neutral source snapshot](../../../../workspaces/previews/canonical-fs-v1/README.md): 533 selected files.
- [Source accounting](packet/SOURCE-INDEX.json) and [notice bindings](packet/NOTICE-BINDINGS.json).
- [Evaluation protocol](../../../evaluations/README.md).

Original checksums/indexes still refer to the unchanged extracted envelope;
use delivery.json for remapped tree paths. Its inner directory name contains
internal: an artifact coordinate, not another authority or installation rail.
Historical source READMEs, seed/resident examples and producer nonclaims are
provenance, not customer instructions. Follow this page and WORKFLOW.md instead.

Keep all legal files, source archives and attribution with the software.
Aware's Apache-2.0 policy does not replace upstream terms. Pathspec's MPL terms
and corresponding source remain attached; r-efi's carried AUTHORS contains the
MIT alternative. Native-component accounts are conservative, not exact linkage
or toolchain proof. The derived jsonschema recipe and publisher source URL/hash
are attached; its original source archive is not. Reproducible builds, exhaustive
secret detection, rights warranty and isolated benchmark scores are not claimed.

Layout review does not select software, freeze instructions, transfer, publish
or authorize a push. The existing public agent contract remains unchanged.
