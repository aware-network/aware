# Neutral Agent CLI composition

The source composition supplies one `aware` entrance over the accepted family
registrars and Kernel's command runtime. It is a composition library with a CLI
entrypoint, not a new Agent SDK, evaluator or authority provider.

```text
aware init --repo-root <absolute-root> [explicit creation/apply options]
aware issue <existing Issue leaf> [original arguments]
aware goal show <explicit committed source arguments>       # optional Goal family
aware goal eligibility <explicit lane/Phase and source arguments>
aware protocol admit [original arguments]
aware protocol setup-specification [original arguments]
aware spec observe [original arguments]
aware spec iteration-identity [original arguments]
aware spec create-draft [original arguments]
aware spec prepare-draft [explicit selections and authored input]
aware workspace setup <original setup leaf> [original arguments]
```

Run `aware --help`, then `aware FAMILY --help` or
`aware FAMILY LEAF --help`. Only the selected family is imported. Each original
registrar supplies its own flags, path meanings, digest guards and result format.
Publication is `aware issue commit-workspace`, the existing Issue SDK operation;
there is no new Repository commit implementation or automatic Issue selection.
SPEC setup previews by default; setup and draft effects require explicit apply
and fresh owner admission. Observation does not approve iterations or work.

This is a breaking successor to public a6's `aware-agent-cli 0.1.0a6`, retaining
the distribution, import namespace and executable identity while moving its
single current authoring home to this Agent library. The old public snapshot
remains historical and unchanged. **This is not an in-place a6 upgrade.**
It does not copy a6's `contract`, repository-create or template helpers. The
successor `init` delegates to the accepted Workspace and Protocol SDKs rather
than retaining a standalone Repository implementation.

## Issue-first initializer source command (default)

Earlier installed candidates qualify initialization independently. This source
successor requires a newly pinned candidate; source changes do not update an
existing installation. For an explicitly selected qualified installation:

```bash
# Validate prospective input and preview; the parent must already exist.
aware init --repo-root /absolute/customer --create-repository

# Explicitly create the empty repository and Issue-only initial profile.
aware init --repo-root /absolute/customer --create-repository --apply

# Bootstrap an existing Git root without changing HEAD, index or remote.
aware init --repo-root /absolute/existing --apply
```

`--repository-root` is an alias of `--repo-root`; both require the same canonical
absolute root. `--issue-root` selects the repository-relative Issue root and
defaults to `docs/issues`. The Protocol SDK prepares every missing ancestor
explicitly. `--no-agent-contract` omits the `AGENTS.md` and Issue protocol files;
the receipt discloses absent onboarding files. Existing targets refuse even
when their bytes match. There is no overwrite, profile upgrade or adoption.
`--dry-run` is explicit preview and cannot combine with `--apply`.

Exactly one genuine Codex or Claude harness session must be present. The command
does not accept a caller-built actor/admission, use a cached execution or change
provider identities. This is harness correlation, not authenticated actor-action
issuance. The SDKs enforce the actual process/execution and single-use authority.

Protocol prepares and validates all input before repository creation. Workspace
then admits and prepares the repository; only after its verified release does
Protocol obtain its fresh plan and admission. An absent-repository preview
reports `prospective_only`, not a live Protocol plan or result. Full success
requires both owners' results and completion. Git success followed by Protocol
failure exits 2 and retains Git creation and partial/unknown Protocol effects.
It never rolls back, automatically retries or restores spent authority.

Default/`--format json` retains full JSON on stdout: exact requests, attempts,
rendered inputs, effects, diagnostics and cleanup for each owner. Explicit
`--format summary` instead prints human answers on stdout: what happened, what
changed, remaining uncertainty, safe next steps and the full-evidence location.
It emits the **complete JSON on stderr in that same invocation**, including
rendered template bodies. This deliberately changes the earlier summary-only
JSON format; machine-only callers should keep using `--format json`.

Retain both streams from the original invocation. Neither a human explanation
nor a stream is an automatically durable receipt store. Do not repeat apply
with another format to recover evidence. This separation is not a claim of less
total output, improved client comprehension or new approval authority.

The summary distinguishes prospective Protocol inputs from admission, known
Workspace creation from a subsequent Protocol failure, and original cleanup
uncertainty from any later cleanup. Untrusted paths are visibly escaped without
changing their SDK values. Summary reporting attempts each output channel once;
an I/O or encoding failure returns 3 (preserving an already supplied 130), not
permission to retry. Reporting explicitly flushes each channel and closes a
failed buffered stream before shutdown, preventing a delayed pipe failure from
replacing that exit with 120. The other channel is still attempted once; closing
a failed output stream is not SDK cleanup or evidence of owner completion.
Owner operations retain their existing 0/2 outcomes,
including the initializer's existing caught-interruption behavior. JSON mode's
transport remains unchanged.

The initial profile is
`aware.collaboration.fs_v1`, with only Issue authority; SPEC, Goal, Feed and
Evidence remain unavailable until their separately governed configuration.
Init creates no Issue, seed commit, index staging, remote, user configuration,
Agent session or service.

Package membership comes from the existing `portable_protocols` checkout
profile, via Agent's module-owned `agent_cli` Code entry and ordinary dependency
metadata. It does not select the full Agent module/Workspace, import Agent
ontology or require its Service-facing SDK. `aware.protocol.toml` configures
customer records and authority; it does not select software packages.

Missing registrar exports refuse before operation dispatch, without another
environment, PATH discovery, raw writer or Service/FS fallback. Generic context
is not execution identity, Issue admission or authorization. The composition
does not refresh guards or retry a failed publication. Family diagnostics and
unknown/applied effect evidence remain unchanged.

## Optional Project/Goal family

The source-only `goal` extra selects Goal's original create-first registrars:
`aware-agent-cli[goal]`. Base dependencies and the `portable_protocols` release
selection do not acquire Goal implicitly. Bundle must qualify a successor
installation before consumer adoption; help availability is not installed
capability. A missing optional registrar refuses without installing it.

For a qualified successor, `aware goal show` and `aware goal eligibility` use
explicit `--repository-root`, `--protocol-manifest` and `--goal-path` inputs;
eligibility also requires `--lane-key` and `--phase-key`. See the Goal-owned
[command journey](../../../../../../aware_coordination/modules/workflow/sdks/goal/python/native_cli/README.md).
They start from an already qualified committed native Goal and committed native
Protocol configuration, not Issue-only initialization. Neither command prepares,
upgrades or repairs configuration. These Phase reads never create/import Goals;
the explicit create-first profile below separately creates Proposed planning
intent. General import and execution remain unsupported.

Goal's owner-qualified reading retains committed associated Issue inputs.
Discovery and eligibility are composed once at an exact repository epoch;
authority changes refuse without silently refreshing. Summaries are descriptive
and label suggested next steps. Eligible never means authorized to RUN, and
these reads admit no Work, approval, event or dispatch. The Agent command only
mounts the original handlers; it supplies no Goal interpretation or provider.

## Draft guard preparation

`aware spec prepare-draft` composes Protocol manifest admission and its read-only
target-fit SDK observation, then the existing Issue read projection and SPEC
input-observation ports. It decodes and renders through the original SPEC
functions. It does not construct draft custody, obtain write admission, run
governed preview, create a package or apply anything.

For a separately qualified successor installation:

```bash
aware spec prepare-draft \
  --repository-root /absolute/customer \
  --protocol-manifest aware.protocol.toml \
  --spec-manifest docs/specs/widget/aware.spec.toml \
  --snapshot-json /absolute/customer/inputs/widget.json \
  --issue-ref fb/2026-10-11/widget \
  --author-ref declared-author \
  --authoring-intent-ref customer-draft-intent \
  --client-intent-id customer-draft-attempt
```

Select an already admitted Issue and configured SPEC binding. The command does
not set either up or infer current work. Snapshot input remains an authored
input; preparation does not fabricate it. Relative input paths use the invocation
directory; generated command arguments use the original observer's absolute
input coordinate so a later invocation need not share that directory.

The supplied SPEC manifest must be repository-relative and fit the configured
root and template. For the illustrative `docs/specs` binding, the expected shape
is `docs/specs/<spec-key>/aware.spec.toml`; omitting the key is a mismatch. The
owner supplies the actual configured root, template, expected shape and reason;
Agent does not infer a key or correct a target.

Both summary and JSON show the original target-fit observation. A mismatch,
invalid locator, unavailable binding, stale manifest, unvalidated result or
uncertain cleanup refuses with **no executable preview/apply guidance**. Issue
and input observation do not follow a refused fit. Summary explains the refusal
and retains the original structured evidence; JSON is the complete receipt.
Choose any replacement target explicitly, then prepare and review again.

A match establishes observed binding layout only—not Issue eligibility,
destination availability, semantic approval or future apply success. The default
summary labels the Issue, exact Protocol-manifest and snapshot-input byte guards,
shows observed execution/status/scope and intended member paths, and supplies
complete original `create-draft` preview/apply commands after a match. Review the
authored input, selections and intended members before explicitly choosing either
command. **The printed apply command is never executed by preparation.**
No manual hash calculation or individual digest-copy step is needed.

`--format json` exposes original owner observations, including request-correlated
target fit and verified cleanup, the original SDK-encoded
draft request, member digests and exact argv. This is a presentation of data,
not a saved-plan import API, package catalog, write capability or authorization
receipt. Separate observations are not an atomic repository snapshot or an
exact retained publication plan. Rendered members remain subject to original
staged validation at apply.

The original command revalidates the unchanged reviewed guards and obtains fresh
admission. If Issue, manifest or input bytes change, apply refuses; explicitly
prepare and review again. Never refresh a guard to bypass a refusal or retry a
known publication. Unknown cleanup retains owner evidence and yields no apply
command. Existing family commands and their full mutation receipts are unchanged.

The source composition requires Protocol SDK >=0.3.2,<0.4.0 and FS
>=0.6.5,<0.7.0, and SPEC SDK 0.3.3 and FS/CLI 0.4.3 or compatible successors
within their finite bounds. Missing ports refuse before observation;
there is no private-reader or provider fallback. Source tests do not update an
installed consumer. Bundle must refresh `portable_protocols` and qualify a fresh
offline, checkout-hidden candidate before customer adoption. Assisted setup,
publication and saved-request transport are separate subsequent slices.

Source tests and canonical capture are distinct from a qualified installed
bundle. Do not change a repository's Environment-selected operational CLI or
overlay an evaluated a6 environment based on this source preview. Installation,
source/notice clearance, customer onboarding and publication follow separately.

## Workspace setup source mounting

This source successor mounts only the public
`aware_workspace_command.setup_registration.register_workspace_setup_commands`
registrar. It delegates the exact parsed arguments to the original Workspace
SDK handler through Kernel's command runtime. No broader Workspace router,
checkout, materialization, Service host or publisher is mounted.

For a separately qualified successor installation, read-only architecture
preparation begins with:

```bash
aware workspace setup --help
aware workspace setup repository \
  --repository-root /absolute/prepared/customer \
  --name example --license-expression MIT --preview --json
```

The other original leaves are `workspace`, `module`, `python-package`, `align`
and `locks update|check`. Physical/protocol `aware init` remains separate: it
does not create architecture, select an Issue, align packages or run locks.
A simple application may use a Repository-owned package; Workspace and Module
layers are optional. Source mounting does not establish application correctness.

Original contract `aware.workspace.architecture-setup-command.v1`, complete
receipts and exit codes 0/1/2/3 remain unchanged. Original SDK plan/currentness
and exact allowed-path checks are not Issue authorization. Neither generic
context, a digest, an allowed-path list nor publication afterward substitutes
for a genuine single-use admission.

The original setup mount remains unchanged. The new `review` composition below
uses genuine A1 admission for repository-manifest creation only. It does not
admit broader setup/alignment or A2 lock updates. Those operations require their
separate admissions against actual resolution roots and tool/input identity.
No automatic guard refresh, scope expansion, lock update, retry or rollback is
added.

Workspace locks require an explicitly selected absolute UV executable,
version **0.11.19**. A selected Repository/registered Workspace resolution
root is distinct from package ownership; no executable is inferred or downloaded
by Agent. The original operation preserves completed failures and uncertain
post-effect evidence; inspect it before considering any new operation.

The accepted Agent 0.2.0a9 baseline requires Workspace SDK
`[preparation,setup,setup_admission,setup_review]>=0.2.11,<0.3.0`, Runtime
`[setup_admission,setup_review]>=0.2.16,<0.3.0` and Issue SDK
`[workspace_setup_admission]>=0.10.6,<0.11.0`. The supplier extras select
Workspace FS adapter 0.1.10 and FileSystem >=0.3.8,<0.4.0. No Service extra is
added. Missing ports refuse without provider/environment fallback. This source
cut does not qualify wheels, update shared locks or replace an installed client.

Parent Bundle owns one exact canonical `portable_protocols` capture, joined
installed parity, source/notice carriage and separately authorized delivery.
Qualified predecessor artifacts remain immutable; do not overlay new visible
source on old wheels or rebuild under an old identity.

## SDK carried repository setup reviews

This source successor adds `aware workspace review`. It supports A1 repository
manifest creation, not package creation, A2, materialization or publication.
Use an initialized repository with an active Issue. The evidence directory must
already exist, be private to the effective user and be outside and disjoint from
the repository. Agent does not create, repair or choose it implicitly.

```bash
aware workspace review prepare \
  --repository-root "$repository_root" --evidence-root "$evidence_root" \
  --issue-ref fb/2026-10-17/repository-setup \
  --issue-path docs/issues/2026/10/17/fb-2026-10-17-repository-setup.md \
  --name example --license-expression MIT \
  --actor-ref "$execution_id" --actor-evidence-ref "$declared_actor_evidence" \
  --client-intent-id repository-preview --include-issue-lifecycle
```

Stop and review the original request, preserved scope, full physical-effect
scope and final-file set. `--include-issue-lifecycle` is an explicit choice to
include this task's Issue record in the scope proposal; omit it if those edits
are not part of the approved task. No Issue binding or setup apply occurs in
prepare. Evidence retention itself has explicit private-directory effects.

The returned reference is exact SDK-issued `SetupEvidenceRef` JSON. Reuse that
single opaque value unchanged; do not author a record, copy its guards, extract
a replacement digest, parse Markdown or select a latest file. References are
descriptive coordinates, not permits. The following variables denote the exact
reference values returned by the preceding commands, not file paths:

```bash
aware workspace review scope \
  --repository-root "$repository_root" --evidence-root "$evidence_root" \
  --reference "$first_review_reference" \
  --client-intent-id repository-scope --accept-reviewed-effect-scope
```

This explicit first decision accepts the SDK's exact proposed union of existing
Issue scope and complete physical effects. It preserves other approved work,
retains intent, submits the original SDK-returned Issue scope request once and
retains its actual return. Only a successful original join produces the second
preview. The second-preview intent is deterministically
`<scope-client-intent-id>:second-preview`; it is validated before the scope
mutation and is never changed to work around a collision.

Stop again. Review the second preview, including the intentional Issue-byte
change and any unexpected drift. The apply allowlist is the SDK's exact final
file set, not scratch paths or the complete Issue scope:

```bash
aware workspace review apply \
  --repository-root "$repository_root" --evidence-root "$evidence_root" \
  --reference "$second_review_reference" \
  --client-intent-id repository-apply --accept-reviewed-final-files
```

Apply uses the second-reviewed guards unchanged, retains its intent before the
one original driver call and obtains genuine Issue admission. Staleness means
stop and deliberately prepare/review again; no automatic refresh, retry,
scope repair or partial-plan apply. Success does not commit or close the Issue.

Human output answers what happened, what changed, what remains uncertain,
what is the next observation/explicit decision, and where full evidence lives.
Guidance describes existing SDK requirements; it grants no action or retry.
Both path sets and the exact evidence reference remain available. Original Workspace release,
effect and durability qualifications are shown separately: later complete
client cleanup does not turn an original `release=unknown` into confirmation.
Human paths and request coordinates use quoted, escaped ASCII display; the
original SDK values and full evidence remain unchanged. Long path lists are
explicitly truncated; use `show --json` to inspect all reviewed inputs before deciding.
`--json` returns the separate Agent presentation envelope containing the original
SDK projections and receipts; it does not change full command JSON v1.

`show` accepts a historical **review-record** reference only, without granting
current use. A different execution must obtain its own admission and fresh
reviews after lawful transfer. Refusals and outcomes use `evidence`, not `show`:

```bash
aware workspace review show \
  --repository-root "$repository_root" --evidence-root "$evidence_root" \
  --reference "$review_record_reference"

aware workspace review evidence \
  --repository-root "$repository_root" --evidence-root "$evidence_root" \
  --reference "$exact_sdk_evidence_reference"
```

`evidence` returns original UTF-8 bytes unchanged on stdout, with independent
client cleanup JSON on stderr. `record_contract` identifies the authenticated
container; returned bytes may be its original captured command, not that
container's schema. Both commands require the same explicit roots and exact
SDK-issued reference. Wrong-kind `show` still preserves its actual failure,
retention uncertainty and exit outcome; a reader hint does not clear them.
No Agent file reader, record writer, private plan access or SDK-schema/capture
decoder is involved.

For incomplete retention/cleanup, the human explanation goes to stderr and
**full available JSON remains on stdout in the same invocation**. This does
not promise that the current failure/cleanup was durably captured: a returned
reference may name earlier evidence, or no reference may have been returned.
Do not repeat a mutating command with `--json` to recreate lost output.
The streams are attempted independently once; failure of the explanation
channel cannot suppress the attempted full output. `--json` remains the exact
Agent envelope with no added explanation, and raw `evidence` output is unchanged.
Exit 0 is
completed action/read, 2 refusal, 3 incomplete retention/cleanup/output, and 130
an interruption (with incomplete status when retention is incomplete).
Successful effects and complete client cleanup do not erase incomplete retention.
Preserve known scope/publication effects even when later steps
fail. Inspect durable evidence after lost output; never redispatch to recreate
a receipt. Client release does not delete retained records.

### Current input refusal evidence

The refusal-evidence source successor consumes Workspace's typed current-input
denial, original reads, phase, reference, retention and independent cleanup.
Human output separates these results. A fully retained denial with complete
cleanup remains a refusal, exit 2; this is not a blanket remapping of exit 3.
Spent physical sequences, uncertain capture and unknown cleanup stay incomplete.
A generic physical refusal such as `sequence_request_baseline_changed` does not
by itself prove a spent-reuse cause or rollback of earlier effects. Explain
the original reason narrowly; do not infer a causal classification from prose.

A `SetupRefusalRecord` reference is evidence only, not a review, decision or
admission. Inspect it through `review evidence`; never submit it to scope/apply
as replacement authority. Its `product_dispatch=not_invoked` describes only
the refused action, not historical effects or private evidence writes.

Incomplete retention falls back to full available owner values, including the
detached refusal even when no refusal record was published. A reference may
then describe earlier evidence; do not infer a successful new capture from it.
Codec/presentation failures remain separate and incomplete, not raw-record
fallbacks. Interruptions retain exit 130. No new guard, retry, policy decoder
or authority is created. Original full command JSON v1 stays unchanged.

This source cut still needs independently accepted successor versions/artifacts
and joined installed qualification; existing public installations are unchanged.

### Exact result input and focused history source successor

This source-only successor adds `--reference-from-stdin` to `show`, `scope`,
`apply` and `evidence`, mutually exclusive with `--reference`. It reads one saved
Agent `--json` result and selects only its top-level `/reference`, then uses the
original SDK codec and readers. No custom reference, guard or live continuation
is reconstructed. Status/ready fields in a capture grant no approval. Explicit
roots, client intent and both separate consent decisions remain required.

Capture JSON from the original invocation once; shell redirection saves tooling
output, not an agent-authored record. Do not rerun a mutation to get JSON. If it
was not saved, retain the original inline reference and use the legacy option.
For a separately qualified successor, a saved first result can be inspected:

```bash
aware workspace review show \
  --repository-root "$repository_root" --evidence-root "$evidence_root" \
  --reference-from-stdin --focus scope < /absolute/saved-first-result.json
```

Only after that review, the caller explicitly invokes scope with the same saved
result, a new declared intent and `--accept-reviewed-effect-scope`. Save that
original scope result, inspect its second preview/final files, then explicitly
invoke apply using that result and `--accept-reviewed-final-files`. Do not pipe
prepare directly into mutation or pre-approve a review that has not occurred.
Stale input refuses unchanged; no automatic observation, refresh or retry.

Stdin must be noninteractive binary input, strict UTF-8, exactly one JSON object
with the existing Agent result contract, and at most 2 MiB. Duplicate keys,
non-finite numbers, depth above 64 and more than 65,536 nodes refuse before SDK
client acquisition. Only top-level `/reference` is selected: no nested fallback,
latest-file lookup, alias, file reader or receipt store. Raw `evidence` output
and human explanations are not input frames. SDK limits still apply to the
selected reference. Caller stdin is not closed. A byte limit is not a time
limit: a producer that never sends EOF can block until cancellation.

New transport adds only `reference_input` metadata: fixed source/selector,
observed byte count, EOF observed and full-frame SHA-256 (null until EOF).
A prefix is not a complete capture or authenticated owner evidence. Original
SDK failures retain their reasons; local read/framing refusals exit 2 and input
interruption exits 130 without creating an SDK record or invoking the product.

Explicit `show --focus overview|scope|files|guards` selects a human historical
view; scope and files list every selected original path, guards label original
Issue, authority-manifest and plan guards. Target/context, uncertainty and client
cleanup remain visible. No view observes fresh guards or grants current use.
Explicit focus with `--json` refuses; omitted focus preserves the original output.
Existing JSON defaults and raw evidence bytes remain unchanged. This is not a
semantic summary of arbitrary refusal/outcome captures or a spent-cause diagnosis.

Review reporting explicitly flushes output and closes only a failed terminal
buffer, preserving 3/130 through shutdown. If sole stdout delivery fails before
any stderr use, original values are attempted once on stderr. In the existing
incomplete two-channel mode, each original channel is still attempted once;
loss of its full-output channel does not guarantee complete delivery through
the explanation channel. Retain surviving output and never redispatch to repair
reporting. Terminal stream closure is not SDK cleanup or outcome confirmation.

Version allocation, artifacts and installed proof follow independent source
review. Do not build these changed sources under the accepted a11 identity or
overlay current consumers. Frozen evaluations and inherited qualifications stay
unchanged.
It does not rebuild the immutable 0.2.0a9 artifacts under their existing identity.
# Explicit create-first source candidate (0.2.0a13)

The existing Issue-first default remains unchanged. A separately qualified
installation with the `goal` extra can instead opt into cooperative, local-policy
initial authoring. This source mounting is not a public release or unassisted
customer qualification.

```text
aware init --profile create-first --repository-root /absolute/empty/customer --create-repository
aware init --profile create-first --repository-root /absolute/empty/customer --create-repository --apply --format summary
aware project create home --title Home --repository-root /absolute/empty/customer --protocol-manifest aware.protocol.toml --apply
aware project show home --repository-root /absolute/empty/customer --protocol-manifest aware.protocol.toml
aware goal create release --project home --title "First release" --intent "Make a useful release" --date YYYY-MM-DD --repository-root /absolute/empty/customer --protocol-manifest aware.protocol.toml --apply
aware goal show release --repository-root /absolute/empty/customer --protocol-manifest aware.protocol.toml
```

Preview is read-only. Each apply displays its original live plan and requires
interactive confirmation; noninteractive apply refuses. Create-first init commits
and projects exactly one Protocol fs_v4 manifest, with Protocol-owned default
record roots. `--issue-root`, `--goal-root` and `--project-root` select explicit
alternatives. Unlike Issue-first init, this opt-in includes an initial commit.
It does not install AGENTS.md, set Git identity, add a remote, or create a Project,
Goal or Issue. Customer Git author/committer configuration must already be usable;
missing configuration is an owner refusal, not permission to set it here.

The next **source-only correction** observes effective Git author and committer
through Workspace before preview, at the prospective customer's own Git path.
It does not borrow a parent repository's local identity. Missing metadata
refuses before creation; metadata changed during confirmation refuses without
refresh. The observation is readiness, not frozen commit authorship or actor
authority; later Git/configuration failures still retain original outcomes.
No identity is selected or written, and global configuration is never repaired.

The same source correction adds an original-owner historical read:

```text
aware init --profile create-first --repository-root /absolute/customer --recover --format summary
```

Do not combine recovery with `--apply`, `--create-repository` or new setup roots.
It returns the original retained request and complete publication result,
including failure. Exit 0 means the historical read succeeded, **not** that
setup is complete/current. Missing result remains uncertain; foreign execution,
busy/damaged retention and absent originals refuse. Recovery neither projects
files nor issues retry/redispatch permission. A failed initialized root is not
an absent root and must not be fed back into fresh `init`. A successor write
admission remains separate. These commands are not added to the frozen accepted
installation by editing source; installed qualification must follow separately.

Project creation is empty. Goal creation publishes Proposed undecomposed intent,
then separately publishes Project membership, retaining both receipts. It starts
no work. A planning Goal is **not yet decomposed**, not eligible by empty-set
satisfaction. Existing Phase-path `goal show` and `goal eligibility` remain
original-owner reads. Read commands never prepare or repair configuration.

Initial setup does not adopt existing repositories, create another initial
Project/Goal, or resume an interrupted setup by reissuing authority. Failure after
an owner starts returns uncertainty and all returned receipts. Preserve original
streams; do not repeat mutation for nicer output or to assume rollback. Summary
mode keeps complete original receipt JSON on stderr. Original-owner recovery and
customer retained records remain authoritative; a JSON copy grants no permission.

Unattended creation, self-serve decomposition, Goal approval, pursuit execution,
RUN, public activation and release remain outside this candidate.
