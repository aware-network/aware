# Aware filesystem collaboration with one installed entrance

Status: **Selected Git preview**. Instructions remain draft.
Independent local selection is accepted; actual delivery/acquisition evidence is
recorded in [PUBLICATION.md](PUBLICATION.md). Local authorization is not proof of push.
This breaking successor offers one fresh installation and one `aware` command
for the existing Issue/repository, Protocol setup and SPEC draft/read operations.
It is not an in-place a6 upgrade. Existing selections and bootstrap stay unchanged.

## Install once

Requires Linux x86-64, actual Python 3.12 and Git. Acquire the public source first;
use the exact revision in the delivery record when reproducing a receipt:

```sh
git clone https://github.com/aware-network/aware.git
cd aware
aware_parent="$(mktemp -d /tmp/aware-collaboration.XXXXXXXX)"
aware_env="$aware_parent/env"
/usr/bin/python3.12 protocols/collaboration/previews/canonical-agent-fs-v1/install.py \
  --python-executable /usr/bin/python3.12 --venv "$aware_env"
AWARE="$aware_env/bin/aware"
"$AWARE" --help
"$AWARE" issue --help
"$AWARE" protocol --help
"$AWARE" spec --help
```

Choose your actual Python executable explicitly. The installer checks the exact
envelope/payload and retains the complete source and legal attachments, then
delegates to the unchanged shipped offline installer. After acquisition no
network, editable imports or Aware development checkout is needed. Existing
targets and symlinks refuse; private-parent permissions remain unchanged.
Never overlay a6 or another preview, combine wheelhouses, or use source launchers.
Failed installation may retain a partial environment and evidence, not rollback.
`consumer-lock.json` is accounting, **not a pip requirements file**.

## Start with prepared inputs

**No `aware init`, repository/profile initializer or automatic guard discovery
is provided in this successor.** Do not copy the older a6 `aware init` recipe
into this environment or silently switch commands to make it work.
The caller needs an exact prepared Git repository, an owner-admitted
`aware.protocol.toml` supporting the Issue and SPEC workflow, a real execution,
Git author configuration and a customer-approved outcome. Without these inputs,
stop and report the preparation gap; do not fabricate authority records.
Cross-candidate bootstrap equivalence and unassisted onboarding remain unproved.

Read [the workflow and guard meanings](WORKFLOW.md), then installed `--help`.
Use **`aware issue`**, **`aware protocol`** and **`aware spec`** from this single
environment. Family launchers remain installed for parity diagnostics, not
separate customer toolchains. Each command delegates directly to its original
SDK registrar/handler; the Agent library adds no policy, parser or writer.

The [opt-in agent template](AGENTS.template.md) is a proposal, not a frozen
contract or automatic bootstrap. It must not overwrite an existing AGENTS.md.

## Capabilities and boundaries

Issue content/progress/scope, scoped Git publication and closeout retain the
existing owner. Protocol admission is observational; SPEC setup prepares only
admitted directories and manifest binding. Governed SPEC draft preview/apply
validates staged semantics and publishes without overwriting an existing package;
fresh observation reads it. Repository publication and Issue closeout are separate.

Default JSON retains full evidence. Issue's optional summary is presentation,
not authorization or a claim that giant-history receipts are solved. Typed
refusals retain guards, effects and cleanup uncertainty. Known publication must
never be automatically retried. Actor strings are not authenticated actions.
Currentness checks observed state; every-write detection, continuous confinement
and hostile-process isolation remain unsupported.

No approval, approved-iteration authoring, import, durable iteration-to-Issue
binding, Goal operation, dispatch, Service/API, ontology/ORM or Experience is
offered by this composition. Historical read-only Goal tooling is separate.
This layout is not a completed consumption-alignment or customer U/V/R receipt.

## Exact source and notices

Workspace's authored **`portable_protocols`** profile is the sole software
selector. This page maps its accepted artifact: no second package registry,
dependency pruning, solver or operation rail. `aware.protocol.toml` configures
customer records and authority, **not distribution packages**. Generated JSON
maps and locks are evidence, not agent-authored selection inputs.

- [Complete accepted envelope](distribution/canonical-agent-source-notice-review-v1.tar.gz), SHA-256 `49fd470e4aadf564ec40131f1bffbe95d0f8d65cf0946e60db07dfd88c09531d`.
- Payload SHA-256 `db23274dcc05c3923c9f7ba33f6bf0d1cbda3717aa120d44ee74ef4d35297b11`: 32 packages, including 19 Aware packages.
- [Delivery map](delivery.json): all 871 envelope members and public paths.
- [Neutral source snapshot](../../../../workspaces/previews/canonical-agent-fs-v1/README.md): 549 exact profile files.
- [Source index](packet/SOURCE-INDEX.json) and [notice bindings](packet/NOTICE-BINDINGS.json).
- [Evaluation protocol](../../../evaluations/README.md).

All licenses, attribution, corresponding source and component attachments travel
with the software—not wheel-only delivery. Aware's Apache policy does not replace
upstream terms; pathspec's MPL and source, r-efi's MIT alternative, schema notices
and conservative native-component coverage remain intact. Exact binary linkage,
publisher toolchain identity, exhaustive secret detection and legal warranty are
not claimed. The source-derived jsonschema recipe and source URL/hash are attached;
its original source archive is not. Reproducible wheel builds are not established.

Original indexes/checksums are relative to the unchanged extracted envelope;
use `delivery.json` for remapped paths. Internal artifact directory names and
historical source READMEs, seed/resident examples and producer nonclaims are
provenance, not customer instructions. This README and WORKFLOW describe the
selected prepared-input entrance. Earlier layout/delivery records retain
their historical unselected status; this presentation does not retroactively
change them. Local selection does not freeze instructions. The separately
authorized Git delivery record binds actual push and revision-pinned acquisition;
no registry release, stable contract or bootstrap migration is implied.
