# Neutral Agent CLI composition

Source preview **0.2.0a5** supplies one `aware` entrance over the accepted family
registrars and Kernel's command runtime. It is a composition library with a CLI
entrypoint, not a new Agent SDK, evaluator or authority provider.

```text
aware init --repo-root <absolute-root> [explicit creation/apply options]
aware issue <existing Issue leaf> [original arguments]
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

## Initializer source command

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

JSON retains exact requests, attempts, effects, diagnostics and cleanup for each
owner. `--format summary` omits only rendered template bodies, keeping their
paths, byte digests and modes and every result/error field. It is not a new
approval or receipt authority. The initial profile is
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

**Governed setup remains held pending real A1/A2 joins:** A1 admits architecture
and alignment effects, including parent registrations, metadata and directory
effects; A2 separately admits lock updates against their actual resolution
roots and tool/input identity. Local source tests demonstrate the existing
Workspace capability, not those admissions. This source cut publishes no
governed apply recipe and grants no new authority. No automatic guard refresh,
scope expansion, lock update, retry or rollback is added.

Workspace locks require an explicitly selected absolute UV executable,
version **0.11.19**. A selected Repository/registered Workspace resolution
root is distinct from package ownership; no executable is inferred or downloaded
by Agent. The original operation preserves completed failures and uncertain
post-effect evidence; inspect it before considering any new operation.

Agent requires SDK `[preparation,setup]>=0.2.7,<0.3.0` and the registrar-bearing
runtime `>=0.2.10,<0.3.0`, without the Service extra. Missing ports refuse
before dispatch, with no provider or environment fallback. This does not qualify
new wheels, update shared locks or replace an installed client.

The accepted setup FS 0.1.5 wheel remains an exact artifact input; its current
expanded source tree must not be rebuilt under that old identity. Full workflow
FS 0.1.6 qualification remains separate. Parent Bundle owns exact canonical
`portable_protocols` capture, installed parity and eventual delivery after the
relevant authority gates. The accepted Agent 0.2.0a4 target-fit correction can
be delivered independently; do not couple it to this held governed setup cut.
