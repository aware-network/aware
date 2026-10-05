# SPEC consumer protocol preparation

Status: **proposal, not shipped support or an approved Specification**.
Issue: `fb/2026-10-05/specification-consumer-protocol-plan-v1`.
Owner: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`.
Machine-readable evidence: [readiness.json](readiness.json).

## Useful value, incremental guarantees

Issue plus scoped commit remains the low-friction entry point. SPEC adds a durable
team agreement: what is being built, its invariants and phases, and how an exact
iteration relates to bounded Issue work. Do not require SPEC for a small Issue.
Goal coordination remains separate; Service/API and Experience are not prerequisites.

The next candidate should expose only a complete, demonstrably usable slice:
observe a selected canonical SPEC and its exact iteration identity; subsequently
create an unapproved draft through governed tooling. A qualified-input reader can
be independently useful, but cannot be called self-serve SPEC-driven execution.
The full loop needs supported approved-iteration authoring/import, durable Workflow
association and publication-time guards. None is supplied by the current reader.

This plan prepares that translation; it does not build or choose a release.
The matrix is derived from owner contracts, **not a new operation registry**.
Future interfaces invoke those operations; they do not read this JSON as authority.

## Pinned source, separate public baseline

Source anchor: `aware-network/aware-dev` at
`21f817f59255b2d2d255e9ae3d8a0ba7062034fe`, handoff
`d42b2ba5d0fc2e7ff6e836b361e9f0f519931c72`.
Protocol independently reviewed that source/supplier cut: **190 passes, zero skips**,
neutral supplier registration, unchanged Kernel projection and offline lock check.
Those receipts accept source, not an installed consumer, approval or binding writer.
The owner repository is a maintainer coordinate, **not a customer download dependency**.
Six supplier manifests, eleven operation/source/adapter files and the carried schema are
byte-pinned in `readiness.json` for owner-side replay. Source exposure must later
use an approved public coordinate and allowlisted neutral `workspaces/` contents.

Public a6 remains `0.1.0a6`, contract `aware.agent.fs.v1 / 1.2.1`, 22 payload
packages. Its supported entrances are `aware` and `aware-issue-cli`.
`aware init` declares Specification **unavailable**, despite recognizing its
record-family name. No SPEC command is shipped in that bundle. a6's exact manifest
and archive hashes remain pinned in the readiness record; no payload changes here.

## Capability mapping

| Source-supported entrance | Existing semantic owner | What it actually does | Customer readiness |
| --- | --- | --- | --- |
| `aware-spec observe` | `specification_sdk.observe` → `specification.source.observe` | Strictly observes an explicitly assembled source closure | Protocol composition and installed candidate pending |
| `aware-spec iteration-identity` | SDK observation + runtime `resolve_iteration_identity` | Reports an existing Phase-scoped iteration ref/revision/plan digest | Qualified input only; no new SDK operation or exported capability |
| `aware-spec create-draft` | `specification_sdk.create_draft` → `specification.draft.create` | Creates one absent canonical draft **with no iterations** | Write governance, input/setup and installed proof held |
| `SpecificationFsSdkProvider.admit_iteration` and original-provider source port | Specification FS owner | Retains/revalidates genuine in-process source admission | Library integration, not transferable JSON authority |
| `IssueSdkOperationClient.observe_specification_iteration_binding` | `issue_sdk.observe_specification_iteration_binding` → `workflow.issue.specification_iteration_binding.observe` | Checks proposed pairing using actual Protocol/SPEC/Issue/Git reads | SDK/provider-only; no pairing CLI or installed customer admission |

The source executable's name is **`aware-spec`**, not `aware-specification`.
Its observation commands accept explicit `--source-base`, repeated `--root`,
optional `--expected-source-digest`, and an exact `--iteration-ref` where applicable.
Draft creation additionally requires a canonical semantic snapshot JSON, author
and intent. These are source-stage contracts to inspect, **not installation or
customer command instructions**. Current raw-root entrypoints do not yet compose
the public Protocol admission boundary. Do not advertise an `aware spec` wrapper
or pairing command that does not exist.

Absent capabilities remain explicit: approved-iteration creation/import, existing
SPEC amendment, durable iteration→Issue binding, SPEC-guarded publication and
trusted Phase acceptance. Draft `iteration_approval_writer_unavailable` and the
absence of a writer demonstrate unavailability, not enforced approval policy.

## Version and filesystem profile proposal

Retain the real `aware.protocol.toml` and existing `specification_fs_v1` carriage;
do not invent a portable-specific manifest, parser or flattened SPEC record.
The proposed first SPEC-capable setup can use the existing
`aware.collaboration.fs_v1 / semantic_version = 1`, which already names this
record family, with an explicitly opted-in Specification authority binding:

- customer-selected repository-relative record root;
- exact `<spec-key>/aware.spec.toml` path template;
- `aware.spec.toml` with `aware = 1` and `specification.profile = specification_fs_v1`;
- strict manifest-owned membership/paths plus the required Markdown projections;
- explicit assembled roots, never dependency-driven discovery; and
- independently declared Issue authority, without enabling Goal or FEED.

`<spec-key>` is a location slot, not permission to reinterpret a folder name as
the manifest's semantic Specification key. `SPEC.md` remains the Human entrypoint;
the manifest and declared Markdown together form the semantic package.
Legacy structure is not silently canonicalized: upgrade-required stays distinct
from malformed or foreign profiles. No automatic migration or manual authority
editing is an onboarding route. Prose, checkboxes and administrative sign-off
cannot establish Phase acceptance.

This is a reuse proposal, not final profile admission. If new persisted semantics
are needed, version them under their actual owners and review the public mapping.
Do not reuse `fs_v2` (native Goal) or `fs_v3` (Project) just to count product releases.
The product release, agent contract, collaboration profile, SPEC record family,
individual SPEC semantic revision and evaluation schema are different versions.
No new version is allocated by this plan; a6 and its bootstrap are not rewritten.

Before customer use, Protocol must provide a fresh admitted selection bound to
repository identity, exact manifest bytes and the allowed root/template. The
selected composition must revalidate it at use; caller-built decoded bindings,
matching digests or raw paths are not equivalent authority. The exact retained
selection interface needs Protocol/SPEC owner agreement. Do not alias a Goal-only
resolver capability as Specification authority or copy its domain provider.
Service authority is unavailable; files owned by a service cannot become writable
because that service is absent or a local CLI is available.

## Setup, drafting and pairing are different gates

1. **Setup:** implement an explicit tooling-based opt-in for the chosen SPEC root,
   missing parent preparation and versioned instructions. Preserve existing
   customer manifests and AGENTS content; inspect refusal/partial effects rather
   than overwriting them. No such SPEC setup operation currently ships.
2. **Observation:** the existing parser/lowerer remains the only interpretation.
   Source/context/snapshot/plan digests are different evidence coordinates.
3. **Drafting:** prepare complete typed semantic input through a supported route.
   Input JSON is a request, not a second record SSOT or an approved iteration.
   Customer authorization and exact Issue source scope must precede filesystem
   mutation through a reviewed composition using the existing owners. Raw author
   and intent strings do not enforce Issue scope. Do not call `aware-spec
   create-draft` a governed Agent writer merely because its target is absent.
4. **Qualified iteration:** accept only explicit owner/customer-qualified input;
   fixture generators, manual record edits and snapshot JSON cannot mint approval.
   The CLI's `retained_capability_exported=false` is real: a later process must
   obtain fresh original-provider admission, not reconstruct it from a transcript.
5. **Proposed pairing:** the existing optional FS composition requires that real
   live admission. It compares every member of every selected closure with
   committed regular Git blobs at the expected HEAD and independently reads the
   Issue (which may be uncommitted). Before returning it rechecks SPEC, Issue,
   manifest, HEAD and repository topology. Result flags remain `binding_persisted`,
   `approval_verified` and `work_authorized` **false**. This bounded sequential
   observation is not cross-owner atomic isolation or future publication authority.

A persisted writer must enforce **one Issue per code-change iteration** across
intent IDs, plan revisions and plan digests. Different iterations may coexist;
no reverse one-to-one or global current iteration is imposed. Owner handoff and
correction of signed work require a new iteration, preserving signed history.
The read-only reader may inspect two proposed Issues without occupying that slot.
Free-text SPEC/Phase/Iteration pointers are not admitted bindings.

The repository owner must later consume/recheck SPEC/Issue/manifest guards **inside
publication**, with the relevant epoch and honest applied/unknown failure effects.
Neither a Workflow precheck nor Git ref CAS alone provides that stronger guarantee.
Issue closeout and ordinary scoped publication remain useful in a6, but do not
prove SPEC-currentness enforcement or create Specification acceptance.

## Prospective neutral packaging boundary

The six pinned Specification projects are:

| Package | Responsibility | Authored mandatory dependency edges |
| --- | --- | --- |
| `aware-specification-runtime` | Meaning, identity and neutral decisions | None |
| `aware-specification-fs-source-contract` | Portable source evidence | None |
| `aware-specification-fs-adapter` | Strict existing source observer/parser/lowerer | Source contract, runtime, `jsonschema>=4.23.0,<5.0.0` |
| `aware-specification-sdk` | Typed public provider operations | Runtime |
| `aware-specification-fs-sdk-adapter` | Separate FS provider and canonical schema | SDK, FS adapter |
| `aware-specification-cli` | Thin exposure | SDK, FS SDK adapter |

All six authored versions are `0.1.0`, Python `>=3.12`. These source versions
are not accepted wheel identities. Build dependencies and test/development extras
are not payload requirements. The Code catalog registration test is a test-tool
dependency, not a reason to ship the Code/ontology runtime. `jsonschema` is already
present in a6 as the notice-reviewed source-derived build; Bundle must resolve the
actual combined constraints and keep its provenance/omission treatment explicit.

For pairing, the Issue FS adapter has an optional `specification` extra selecting
`aware-specification-fs-sdk-adapter`. Ordinary Issue imports/mandatory dependencies
stay independent. Exposing pairing needs new pinned SDK/provider wheels plus its
supported entrance, not merely adding six wheels to a6. Internal Issue source
versions differ from the derived public wheel versions: do not substitute or
downgrade them silently. Preserve a6's supported exports/usability through an
explicit owner-reviewed source projection and version boundary.

The final consumer closure is **unknown until independently resolved and audited**;
there is no "28-package acceptance" by arithmetic. The Kernel 243-package lock is
internal development evidence only. No aggregate workspace lock, generated API,
service, DTO, ontology/ORM, Experience or materialization is a consumer input.
Required neutral source belongs in allowlisted `workspaces/`; operational docs,
contracts and delivery/evaluation assets belong in `protocols/`.

Bundle must inspect actual wheel contents, import/resource paths, Python bounds,
entrypoint ownership, reachable dependency edges, source coordinates and legal
files. In-wheel notices/license metadata and exact schema coverage need new
candidate review; earlier a6/Goal clearance is not automatic SPEC clearance.
Declaration of an entrypoint does not admit it as a supported customer interface.

## Installed acceptance obligations for the selected slice

| Obligation | Real owner/path to exercise | What is not a pass |
| --- | --- | --- |
| Fresh offline installation | Exact candidate and shipped entrypoint, with development checkout hidden, networking disabled and environment cleared | Source imports, inherited editable environment or a new test classifier |
| Explicit SPEC setup/admission | Actual Protocol composition; preserve existing manifest/bootstrap and refuse unsupported authority/profile | Manual manifest patch, decoded DTO or service-to-FS fallback |
| Custom root and strict carriage | Existing SPEC observer/parser with real in-wheel schema | Fixed `docs/specs`, schema-only acceptance or checkout resource fallback |
| Exact iteration identity | Runtime identity through SDK observation | Title/recency guesses or Gate/approval inferred from the plan digest |
| Genuine source admission | Original provider lifetime/revalidation; forged, copied, released, closed, restamped and cross-provider cases | Serialized JSON presented as capability |
| Committed-source and return horizon | Every explicit closure; missing/dirty/symlink/submodule/duplicate sources; actual HEAD, Issue and manifest changes | Stable semantic digest waiving exact byte drift or a permanent-authority claim |
| Proposed-pairing result integrity | Actual SDK/provider; malformed, incomplete, uncorrelated and authorizing-result probes | Copied refusal rules in the harness |
| Non-authority and preservation | Read closed/foreign/unassigned Issue without admission; preserve foreign staging/dirty files | Voluntary Agent restraint claimed as enforced scope control |
| Draft slice, if selected | Real Issue/Protocol composition plus existing no-replace draft primitive; preserve applied/unknown effects | Raw-root writer, fabricated approval, or blind retry after publication |
| a6 compatibility | Existing Issue/commit loop, summary publication fields, closeout and setup | Replacing its accepted receipt with only new SPEC tests |

Approved-iteration writers, persistent cardinality enforcement, SPEC-guarded
publication and Phase acceptance are **unsupported until separately implemented**,
not negative tests counted as policy enforcement. If these are omitted, freeze
instructions for the narrower reader/draft capability only. Do not claim the full
SPEC→iteration→Issue execution loop or distributed transaction safety.

## Next owner sequence

1. Protocol and Specification/Workflow review this mapping and explicit selection,
   setup/write/input gaps. Evaluation independently synchronizes its own package
   manifests/locks; its progress does not admit a public package closure.
2. Open bounded owner integration cuts for supported public admission/setup and
   the chosen slice. No copied engines; unavailable writers stay unavailable.
3. Bundle builds/version-pins the selected neutral source/CLI closure and reviews
   exact legal/resource/source content into a new immutable candidate.
4. Protocol replays installed positive/adversarial obligations against those
   exact bytes; independent review accepts the stated capability boundaries.
5. Freeze consumer instructions and run a separately approved external evaluation
   using the public v2 format and optional evaluator tooling. U is frozen before V;
   fresh R consumes durable records, not prior transcripts. Partial/unsupported
   results remain explicit. No template is an answer key.
6. Public content, source availability and target-specific publication authorization
   precede delivery. No push, promotion, registry release or customer upgrade here.

## Preparation checks

Run the standalone public plan checks; they verify mapping consistency and a6 pins,
not domain enforcement or candidate installation:

```sh
/usr/bin/python3.12 -I -B protocols/specification/test_readiness.py
```

Maintainers may additionally verify all owner-source pins and authored package
metadata against the exact Git revision without installing or importing it:

```sh
/usr/bin/python3.12 -I -B protocols/specification/test_readiness.py \
  --owner-repository /absolute/aware-dev
```

The private owner checkout is needed only for this maintainer provenance check,
never for the eventual customer bundle. A public source/rebuild input has not yet
been exported. These checks and readiness JSON grant no operation authority.

### Local preparation receipt

Executed with Python 3.12.3:

- **24 preparation checks passed**, including a standalone run without the owner
  checkout argument and a maintainer replay matching all **18 committed blobs**
  (six supplier manifests, eleven source files and one schema resource).
- **112 adjacent checks passed**: 42 evaluator-tooling, 16 evaluation-format,
  35 publication/layout and 19 a6 accounting checks.
- Ruff formatting/lint and `git diff --check` passed.

That is **136 distinct passing checks**, not 136 installed SPEC cases. No SPEC
runtime execution, candidate build/installation or external evaluation ran for
this plan. The 190-case source review above is separate supporting evidence,
not added to this count. Independent plan review remains pending; a6 delivery
bytes and the existing consumer contract are unchanged.
