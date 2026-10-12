# Aware

Coherent work between agents in your Git repository.

Aware provides shared rules and tooling so agents understand the same work,
make bounded changes and leave evidence another execution can continue from.
Issues coordinate work; Specifications describe its intended shape. Coherence
is the value, not a promise of faster agents or conflict-free swarms.

Aware's direction: Don't watch your agents. Watch your goals. See [aware.run](https://aware.run).

The target-fit software is published at
[`2a805bd45535089513f657b7ff0acffe4e54d697`](https://github.com/aware-network/aware/tree/2a805bd45535089513f657b7ff0acffe4e54d697).
One installation supports init, Issues, SPEC setup, target-fit preparation and
draft preview/apply/read. [Delivery status](releases/canonical-target-fit-fs-v1/PUBLIC-STATUS.md)
separates that delivered software from this local status-only alignment, which
awaits independent review and separate publication authorization. The
[delivery pointer](releases/SELECTED.json) binds the exact whole envelope;
[successor instruction pins](releases/canonical-target-fit-fs-v1/PUBLIC-INSTRUCTIONS.json)
preserve the accepted commands and guards. Do not overlay installations or
silently migrate contributor commands.

## Understand the shared rules

Read [coherence](protocols/COHERENCE.md), [Issues](protocols/issues/README.md),
[repository publication](protocols/repository/README.md) and [SPEC drafts](protocols/specification/README.md).
Readable protocols explain shared rules; tooling applies separately admitted
operations. Installing tooling, configuring a repository and starting a service
are different decisions. This filesystem composition starts no service.

## Inspect terms and install once

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Read
[complete distribution terms and source](releases/canonical-target-fit-fs-v1/README.md)
before installing. Keep LICENSE, NOTICE, corresponding source, upstream inputs
and raw audit with the software. Six package-local legal gaps remain unresolved;
detached wheels, stripped bundles and registry publication are unaccepted.

From this reviewed checkout root:

```sh
set -eu
aware_parent="$(mktemp -d /tmp/aware-consumer.XXXXXXXX)"
aware_init_env="$aware_parent/env"
test ! -e "$aware_init_env"
test ! -L "$aware_init_env"
/usr/bin/python3.12 protocols/install.py \
  --python-executable /usr/bin/python3.12 --venv "$aware_init_env"
AWARE="$aware_init_env/bin/aware"
"$AWARE" --help
```

After acquisition installation is offline. The original installer verifies and
retains the whole envelope, including terms and source, before delegating to its
payload installer. It returns the absolute `retained_source_and_notices` directory.
Keep it; set `aware_envelope_root` to that exact directory for the typed example.
Reuse refuses. No editable checkout or development source is required.

## Initialize and admit work

Use your genuine harness with exactly one nonblank `CODEX_THREAD_ID` or
`CLAUDE_CODE_SESSION_ID`. Do not fabricate or borrow identities. Set
`aware_repo_root` to an explicit absolute target under an existing parent:

```sh
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

New targets must be absent or empty. For existing Git repositories omit
`--create-repository`. Preview supplies Workspace preparation and prospective
Protocol inputs, not two admitted plans. Apply obtains fresh Protocol admission
after repository preparation. Existing configuration/guidance refuses.
Init normally prepares Issue directories, `aware.protocol.toml` and readable
`AGENTS.md`; read them. It stages nothing, creates no seed commit or remote,
opens no Issue, approves no SPEC and starts no service. Preserve both owner
receipts, effects and cleanup. Nonzero exit is not rollback or permission to retry.

`--issue-ref` is `fb/YYYY-MM-DD/lowercase-hyphenated-slug`, not a UUID, title or
Markdown path. Follow [the first-Issue example](protocols/issues/FIRST-ISSUE.md)
to create the record, observe its exact bytes, bind scope and start progress.
Choose outcome and scope first. Missing identity, invalid references and stale
guards refuse; retain diagnostics rather than guessing or silently refreshing.

## Check target fit then review and invoke

Use [the complete workflow](protocols/WORKFLOW.md) for Issue-governed SPEC setup,
typed input preparation, draft preview/apply and observation. No prequalified
package or approved iteration is needed. One 42-package installation supports
`aware issue`, `aware protocol`, `aware spec` and explicit `aware init`.

`aware spec prepare-draft` first asks the original Protocol SDK whether the
supplied SPEC manifest fits the configured layout. Review the configured root,
template, expected shape, supplied target and owner reason. For an illustrative
`docs/specs` root, `docs/specs/json-checker/aware.spec.toml` includes `<spec-key>`;
`docs/specs/aware.spec.toml` omits it. Your observed binding governs, not the example.

A mismatch refuses without preview/apply guidance or subsequent Issue/input
observations. No key is inferred or target repaired. A match establishes observed
layout only—not Issue eligibility, destination availability, semantic approval
or guaranteed publication. Do not interpret `prepared` as write admission.

For a matching request, preparation labels Issue bytes, Protocol-manifest bytes
and input bytes, shows observed owner/lifecycle/scope and intended members, and
prints separate original preview/apply commands carrying unchanged guards.
Add `--format json` for full observations and exact vectors.

Preparation is read-only assistance, **not write authority or an atomic snapshot**.
Review the evidence, explicitly invoke preview, review its result, then separately
decide on apply. Use the installed absolute executable instead of printed leading
`aware`; preserve every other argument and guard. Never `eval` the lines, execute
vectors automatically, refresh guards while copying or retry a mutation. Stale
state requires preparation and review again. Manifests are repository-relative;
explicit absolute snapshot paths avoid cwd ambiguity. The three guards identify
different bytes; normalized semantics cannot replace exact-byte currentness.

## Publish and preserve evidence

Use [guarded publication and paired closeout](protocols/WORKFLOW.md#paired-publication-and-closeout).
Select exact admitted paths, configure an explicit Git author and dry-run before
identical apply. Preserve foreign work. Publication and closeout are two effects,
not atomic: late refusal may follow known publication. Keep commit/reference
update, index, closeout, cleanup and known/unknown effects. Do not republish to
recreate spent authority or assume rollback. Remote push is separately authorized.

## What comes next

Issues → Specifications → Goals → shared map. Approval, approved iterations,
durable binding, Goals tooling, service elevation and object/materialization
bridges are not supplied here. Workspace's standalone script is carried, not
admitted as an Agent mount or governed workflow; `aware workspace` is unavailable.
Workspace deltas are change evidence, not meaning or authority. Currentness is
observed state, not every-write detection or continuous confinement. This
successor still needs fresh unassisted evaluation.

[Sources](workspaces/README.md) are the canonical `portable_protocols` snapshot,
not another package catalog. Historical source READMEs are not customer guidance.
Contributor governance and its command selection remain separate and unchanged.
