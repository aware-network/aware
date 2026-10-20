# Native Goal CLI

`aware-goal-native` is a thin read-only CLI over Protocol admission, the native
Goal filesystem provider, the public Goal SDK transport, and the neutral Goal
operational runtime. It supports V2/V3 Phase eligibility and whole-document
direction/currentness. It has no raw-root or legacy fallback and grants no
approval, pursuit-running, event, or dispatch authority.

This package is separate from the legacy local Goal SDK and CLI. A new pinned,
locked consumer installation and external evaluation remain separate gates.

## Qualified customer reads (source successor 0.1.1)

The Goal-owned registrar supplies `show` and `eligibility` to both
`aware-goal-native` and, when the optional Goal family is selected, `aware goal`.
No request file, manual digest calculation or discovery invocation is required:

```bash
aware goal show \
  --repository-root /absolute/customer \
  --protocol-manifest aware.protocol.toml \
  --goal-path plans/goals/2026/10/17/goal-2026-10-17-widget.md

aware goal eligibility \
  --repository-root /absolute/customer \
  --protocol-manifest aware.protocol.toml \
  --goal-path plans/goals/2026/10/17/goal-2026-10-17-widget.md \
  --lane-key delivery --phase-key first
```

These examples require an **already qualified, committed native Goal** and a
committed Protocol manifest admitting its root/template and associated Issues.
Paths are illustrative, not a default layout. The manifest path may be absolute
or relative to the explicit repository root. Goal paths and optional
`--prerequisite-goal GOAL_TAG=REPOSITORY_PATH` hints are repository-relative;
each prerequisite still receives independent source qualification. Protocol
owns configuration preparation and profile transitions. The reads never create,
install, upgrade, commit or repair anything and never fall back to legacy roots.
Issue-only `aware init` does not qualify this journey. Creation/import is absent.

`show` returns the existing owner-qualified committed reading, including its
associated Issue and schedule inputs. Dirty local Issue titles are not spliced
into it. Unsupported time, activity and execution-capability facts remain
unavailable. `eligibility` discovers and observes exactly once against the same
repository epoch. An intervening HEAD or manifest change refuses; it does not
rediscover to obtain a successful answer. Explicitly review a refusal before a
new invocation.

Summary is descriptive: prerequisite partitions, missing evidence and suggested
next steps. **Eligible is not authorized to RUN.** `--format json` retains the
complete original reading or request/result and source references. Exit 0 means
an observation succeeded, including a held verdict; refusal exits 2. No approval,
Work admission, event or dispatch results from these commands.

Existing technical discovery, observation and direction commands remain intact.
Source replay is not a qualified installed successor or a registry release.

## Unmounted create-first registrar candidate (source 0.1.2)

`customer_commands.register_project_commands` and
`customer_commands.register_create_first_goal_commands` are isolated registrar
qualification entrances, NOT mounted commands. Neither Agent nor the standalone
launcher selects them. Existing executable read operations above are unchanged.

The candidate transports explicit Project create/show, Proposed Goal create and
separate attachment, and qualified name-based reads. Its Goal registrar delegates
explicit `--goal-path` show and Phase eligibility to the original handlers.
Project show uses qualified H0 or the separate qualified membership/H2 reading;
stale/uncertain membership never becomes an empty Project fallback.

Create defaults to a read-only preview. In this bounded cut, `--apply` requires
interactive input/output: display the complete original plan, then type the
exact `create NAME` confirmation, consuming THAT live plan without recapture.
This is local authoring consent, not Identity or Goal approval. Noninteractive
apply refuses before provider use: there is no supported original-owner durable
cross-invocation review binding yet, and no caller hash/token substitutes for it.
An explicit Goal date is addressing only, never an invented lifecycle timestamp.

Summary output carries complete original JSONL plan/result evidence on stderr
from the same invocation. JSON mode emits complete records on stdout; interactive
confirmation still applies. Reads emit one complete record. Partial/uncertain
results retain complete available owner receipts; exit3 never means rollback or
cleanup. Unexpected failure after initiation is uncertain, never permission to
repeat creation. Shows/help/preview do not install, repair or reissue anything.

The source profile still requires already accepted fs_v4 bootstrap/enrollment
and a supported genuine harness execution; no Human Identity is manufactured.
No bootstrap UI, general import/adoption, decomposition, eligibility-by-empty-set,
approval, pursuit, event or dispatch is added. Narrow dependency metadata is not
consumer lock qualification. Installed/public mounting remains held.
