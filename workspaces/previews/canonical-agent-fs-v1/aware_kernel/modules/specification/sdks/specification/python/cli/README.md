# Specification CLI

Thin source-stage `aware-spec` 0.4.2 entrance; no service probing or fallback.
Existing reader requests and owner behavior remain unchanged. Governed draft preview/application is
an optional source-stage entrance with whole-context completion handling below;
this README does not select a public installation or enable published previews.

CLI0.4 adopts accepted original input custody before constructing the SPEC
context. Independent review accepts the 448-case source replay and three
additional genuine probes, separate from the
historical CLI0.3 early-refusal leak, whose failed receipts are preserved.
Neither source checkpoint selects a consumer installation or claims qualified
authoring. Null/unknown evidence is not permission to retry claimed cleanup.

CLI0.4.1 separately consumes SDK0.3.1/adapter0.4.1 original completion evidence.
Its source qualification/review and refreshed consumer installation are separate
from that accepted custody checkpoint; historical CLI0.4 artifacts remain unchanged.

- `observe --repository-root PATH --spec-manifest RELATIVE_MANIFEST`.
- Repeat `--spec-manifest` in exact UTF-8-byte order for all explicit roots.
- `iteration-identity` adds the exact `--iteration-ref`.
- `--protocol-manifest` defaults to `aware.protocol.toml` within the explicit
  repository; `--expected-manifest-sha256` checks its exact observed byte digest.
- Repository roots may be relative to the invocation directory. Relative
  Protocol manifests remain repository-relative and are resolved once by the
  Protocol issuer; absolute manifest paths pass through unchanged.
- `--expected-source-digest` separately checks the SPEC owner's source closure.

Example source-stage form (not a consumer installation instruction):

```text
aware-spec observe --repository-root /customer/repo \
  --spec-manifest contracts/example/aware.spec.toml
```

The command freshly issues Protocol selection, constructs the real guarded SPEC
provider and reads through the public SDK. It revalidates before printing and
closes its owned provider and selection on every exit. Typed Protocol refusals
do not become SPEC approval or fabricated source observations. Output is portable
evidence with `retained_capability_exported=false`; a later execution must admit
its own sources again.

The mandatory dependencies select public SDK `>=0.3.1,<0.4.0`,
`aware-specification-fs-sdk-adapter[protocol]>=0.4.1,<0.5.0` and the existing
neutral `aware-command-runtime>=0.1.1,<0.2.0`. The adapter's Protocol reader extra
selects `aware-protocol-fs-adapter>=0.3.0,<0.7.0`; the default CLI dependency
set does not select the adapter's `governed` extra or Protocol's `draft` extra.
The CLI's optional `governed` extra explicitly requires
`aware-specification-fs-sdk-adapter[governed]>=0.4.1,<0.5.0`, including the
accepted SDK0.3.1 completion/custody generation through that adapter and Protocol
`[draft]>=0.6.1,<0.7.0`. Its Issue/FileSystem
supplier floors still require Bundle's neutral-profile refresh; internal
workspace distributions are not an admitted consumer closure.
Exact successor installation and predecessor/successor command parity remain
separately qualified by Bundle.
Do not modify or substitute historical CLI 0.2.1 wheels, overlay environments,
or infer a neutral dependency closure from internal workspace metadata.
No Protocol or command-runtime edge enters the neutral public SDK/runtime or
source-value contract.

`aware_specification_cli.read_commands.register_read_commands(registry)` registers
exactly `observe`, then `iteration-identity`, with no IO or provider admission.
The standalone entrypoint dispatches through Kernel's existing neutral registry.
Both projections reference `SPECIFICATION_OBSERVE_OPERATION_REF`; identity adds
the existing neutral resolver, not a second SDK operation. Registration labels
and invocation context are not authority. Duplicate registration refuses; no
writer enters this read registrar. Main additionally composes the separate lazy
`register_draft_commands`; there is no `aware spec` alias or automatic environment
combination. Missing governed integration returns a typed unavailable refusal.
Draft requests never retry through `compatibility_main`, even when the historical
diagnostic writer is present.

Help now describes those two reads through the generic registry. Command arguments,
existing JSON read fields, explicit exit codes and owner cleanup remain
unchanged. Refusals additionally retain owner-supplied diagnostics. Main help also names `create-draft`; read-only mounted help remains
separately tested. Source parity does not imply installed parity.

This is an explicit pre-1.0 CLI source-interface change. Raw `--source-base`/
`--root` are not consumer options, and failure never retries through them.
`compatibility_main` retains historical maintainer diagnostics
as a library function only; it is not registered as a console entrypoint.

## Coordinates and currentness guards

CLI 0.4.2 names these conventions in each command's help; it does not silently
normalize paths, reinterpret guards or add an observation operation.

| Argument | Base or source |
| --- | --- |
| `--repository-root` | Absolute or relative to the invocation directory. |
| `--protocol-manifest` | Absolute or relative to the explicitly selected repository; default `aware.protocol.toml`. |
| `--spec-manifest` | Canonical repository-relative selected `aware.spec.toml`; not absolute, cwd-relative or Protocol-manifest-relative. |
| `--snapshot-json` | Absolute or relative to the invocation directory, independently of `--repository-root`. |
| `--expected-manifest-sha256` | Exact Protocol manifest bytes, **not** the SPEC manifest or normalized Protocol semantics. |
| `--expected-issue-sha256` | Exact Issue document bytes; the Issue owner separately verifies currentness. |
| `--expected-input-sha256` | Exact saved input bytes; preview returns `input_sha256`. Apply requires the reviewed value. |
| `--expected-source-digest` | SPEC owner's source closure; distinct from Protocol bytes, snapshot and source-context digests. |

Input-open failures return `draft_input_open_failed`, a stable reason and
exception-class detail without copying a host exception's filename/body.
`input_guidance` identifies the argument, path base and safe next action.
Read refusals preserve supplied diagnostics; draft refusals keep their existing
primary, effect and cleanup evidence. The CLI does not reconstruct a cause the
owner omitted: Protocol's generic draft-admission wrapper still requires its
separate source correction. No stale guard is refreshed or retried automatically.
Labeled owner-observed guard discovery, concise SPEC receipt presentation and
the unified installed entrance remain separate cuts. This source successor does
not change the accepted 0.4.1 installation or public selection.

## Governed draft: source-only preview and application

Prepare the existing canonical `aware.specification.snapshot.v1` bytes with
exactly one complete definition and no iterations. The executable
[`examples/prepare_draft_input.py`](examples/prepare_draft_input.py) uses public
neutral values, the installed semantic-resolution context and the original
codec. Replace its illustrative meaning with the customer's approved terms.
Run preparation separately and save exact stdout bytes to an explicitly chosen
input artifact; adding a terminal newline, pretty-printing or silently sorting
the wire breaks canonical carriage. The command never executes customer Python
and introduces no YAML/TOML/Markdown meaning converter.

Source-stage form (not public installation guidance):

```text
aware-spec create-draft --repository-root /customer/repo \
  --protocol-manifest configuration/aware.protocol.toml \
  --spec-manifest contracts/example/aware.spec.toml \
  --snapshot-json /customer/input/definition.json \
  --author-ref CUSTOMER_AUTHOR --authoring-intent-ref CUSTOMER_INTENT \
  --client-intent-id UNIQUE_ATTEMPT --issue-ref EXACT_ISSUE_REF \
  --expected-issue-sha256 sha256:ISSUE_BYTES \
  --expected-manifest-sha256 sha256:PROTOCOL_BYTES \
  --expected-input-sha256 sha256:INPUT_BYTES
```

Preview is default. `--apply` explicitly requests the original SDK's publication
and requires the reviewed exact input digest. Input is read once through a
bounded descriptor: a final-component symlink/non-regular file refuses, the
ceiling is 2,097,152 bytes, and observed growth, metadata/identity change or
substitution refuses. This is observed-state currentness, not every-write
detection. Input files carry meaning, not publication authority.

The configured parent must already exist. Protocol admits the explicit target
and manifest; FileSystem supplies the retained no-replace plan and same-parent
scratch; Issue separately admits the harness execution, exact Issue bytes,
owner, lifecycle and scope. Preview enters and exits that genuine composition
without invoking publication. Apply uses the existing renderer, strict staged
validation, physical publisher and correlated reader. Neither path edits an
Issue, stages/commits Git, updates bindings, approves a Phase, creates iterations,
overwrites an existing package or synthesizes Service authority.

**Whole-context completion is required for exit0.** Protocol now supplies genuine
once-only cleanup evidence through original Issue custody and SPEC; a returned
release call alone still proves nothing. Only a normally returned operation and
fully exited original context, correlated original custody, completed physical
and Protocol cleanup, and no primary/secondary diagnostics or residual scratch
qualify `consumer_completion_verified=true`. Independent consumer-read closure
and final currentness failures still refuse even when Protocol completed.

Refusals remain **exit2** with `consumer_completion_verified=false`, the original
typed error and known effects. Otherwise insufficient completion evidence uses
`draft_cleanup_completion_unverified`. Historical `None/unknown` evidence stays
unknown; a dependency upgrade or later test-only disposal never upgrades it.
`protocol_owner_completion` projects the accepted SPEC carrier, not a descriptor
scan or inferred whole-operation status. Missing/unattempted/incomplete/unknown
outcomes cannot produce success. Primary interrupts keep stderr evidence and
their original termination behavior.

The effect/result and original cleanup ledgers remain in JSON; known publication
is never erased by late refusal. Do not automatically retry an exit2 publication.
Reobserve using fresh read admission and inspect cleanup diagnostics/residue.
This source success contract is not installed/public authoring acceptance.

JSON preserves original request/attempt/execution correlation, all ordered
effects, durability/completeness (including null/unknown), residual paths and
primary/cleanup diagnostics. Exact rendered member bytes in cleanup requests
use `{ "encoding": "hex", "body": "..." }` without truncation. Detached JSON
is not reusable authority. Cleanup is attempted only by the original owner;
the CLI never inspects private state or blindly retries a claimed attempt.
Escaping caller interrupts retain cleanup evidence on stderr and propagate;
owner-normalized interruptions remain typed owner refusals.

The CLI obtains genuine original Issue input custody before invoking the SPEC
factory and supplies that same handle. Each attempt has a fresh process-local
correlation; the original SPEC context adds its distinct context reference.
Acquisition failures preserve typed partial-custody evidence. Before a handle
returns, only CLI-created originals are submitted to atomic unreserved owner
release ports: a competing reservation refuses before effects. After custody,
no raw resource release is retried. A factory failure before association uses
the original bare-custody release guard; associated claims refuse there. Known
attempt evidence only suppresses duplicate calls, never authorizes disposal.
`input_custody` is portable evidence, not a reusable handle; all original
resources/claims remain process-local. Real descriptor restoration still needs
candidate-bound installed proof after independent source acceptance.

Reader-only imports and registration do not load governed suppliers. Optional
imports unavailable at invocation refuse without compatibility/service fallback.
Bundle's exact neutral closure, installed input preparation/authoring proof,
source/notices, public selection and external evaluation remain separate gates.

## Historical compatibility input

The input is the existing runtime's canonical snapshot wire containing exactly
one complete definition, no iterations, and the accepted semantic profile.
Use the typed neutral runtime codec to produce it; compatibility diagnostics do not guess
semantic meaning or reinterpret legacy Markdown. The primitive creates an absent draft,
not an approved execution plan. Parent directories must already exist.

Output includes authority mode/grade, source/snapshot digests and semantic
iteration identity. JSON is portable evidence, not the retained SDK capability.
No approval, iteration writer, Issue binding, Git publication or readiness
authority is exposed by the historical diagnostic primitive. Source tests do
not admit the new command in public a6 or any selected SPEC preview.
