# Aware target fit workflow

Locally frozen instructions, pending independent review: install
once, initialize explicitly, admit an Issue, configure SPEC and prepare a draft
for review before explicit invocation. Agent CLI is 0.2.0a4; Protocol SDK/FS are 0.3.2/0.6.5; SPEC SDK is 0.3.3;
SPEC FS SDK adapter and CLI are 0.4.3. Issue CLI 0.8.3 / FS 0.9.4 remain selected.
The locally selected whole distribution carries the exact forty-two-package
payload, committed `portable_protocols` sources and corresponding notices.
[Instruction pins](../releases/canonical-target-fit-fs-v1/INSTRUCTIONS.json)
bind this guidance to those accepted artifacts, not to operation authority.
Public delivery is not yet authorized. Scripted installed proofs do not establish
unassisted customer onboarding.

## Install with the complete envelope

Qualified target: Linux x86-64 with `/usr/bin/python3.12`. Keep this entire
envelope, including LICENSE, NOTICE, sources, upstream archives and indexes.
Wheel-only acquisition is unsupported: six Code/Workspace wheels still lack
package-local legal attachments. Do not discard the envelope after installation.

From this reviewed public checkout root, use the same whole-envelope installer
as the [root entrance](../README.md). It verifies the accepted outer envelope and
inner payload and retains terms, source and notices before installation:

```bash
set -eu
aware_init_parent="$(mktemp -d)"
aware_init_env="$aware_init_parent/env"
test ! -e "$aware_init_env"
test ! -L "$aware_init_env"
/usr/bin/python3.12 protocols/install.py \
  --python-executable /usr/bin/python3.12 --venv "$aware_init_env"
AWARE="$aware_init_env/bin/aware"
"$AWARE" --help
```

The target must be absent and its private parent must exist. Do not overlay a6,
an older SPEC preview or a resident development environment. Use this same
absolute `AWARE` command for every family. Standalone family entrypoints remain
parity/diagnostic entrances, not separate required installations.

Keep the exact absolute `retained_source_and_notices` directory printed by the
installer with the software. Set `aware_envelope_root` to that directory for the
typed example below; do not guess an expanded source path or discard its terms.

These candidate-bound instructions supersede the immutable inner README's older
no-init wording. Selected READMEs with seed, resident or broader-workspace recipes
are source history, not customer directions. The payload is not edited to update
that history. Neither installation nor init starts a resident service.

## Harness identity and explicit initialization

Use your actual supported agent harness with exactly one nonblank stable identity:
`CODEX_THREAD_ID` for Codex or `CLAUDE_CODE_SESSION_ID` for Claude Code. Do not
export fabricated values, copy another execution or borrow a fixture identity.
Missing or ambiguous context refuses. Receipts identify execution; they do not
claim cryptographic authentication or resident-session admission.

Choose `aware_repo_root` as an explicit absolute repository path under an existing
parent. A new target must be absent or empty. Keep the same genuine execution for
preview and apply:

```bash
"$AWARE" init --help
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
```

Preview is the default and has no effects. Review the Workspace preparation
preview (`outcome=planned`) and prospective Protocol inputs separately
(`status=prospective_only`). Those inputs are not an admitted Protocol plan:
`completion_verified=false` and `effect=none`. Apply obtains fresh Protocol
admission after Workspace prepares the repository:

```bash
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

For an existing Git repository omit `--create-repository`; preview before apply.
Existing configuration/guidance refuses without overwrite. Init is not a repair
or migration operation. Inspect help for `--issue-root` and `--no-agent-contract`.

Init preserves both owner receipts. If the second owner refuses after repository
creation, known effects remain; nonzero exit is not rollback. Preserve effect,
cleanup, completion and retry evidence. Do not automatically retry a failed
mutation. Successful init supplies Issue directories, `aware.protocol.toml` and,
by default, readable `AGENTS.md`. Read that guidance first. Init does not admit an
Issue, create a seed commit, stage work, add a remote, approve documents or start
a service. Tool installation, readable guidance and configuration are distinct.

## Issue reference versus record path

`--issue-ref` uses `fb/YYYY-MM-DD/lowercase-hyphenated-slug`, with four-digit year,
two-digit month/day and lowercase letters/digits separated by single hyphens.
Example: `fb/2026-10-11/json-checker-draft`. No `.md` suffix; do not pass a UUID,
title, URL or filesystem path. With the default `docs/issues` root, it maps to:

```text
docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md
```

That repository-relative record path is a `--scope-path`, not an Issue reference.
If you configured a different Issue root, use its mapped record path instead.
The installed help and owner refusal diagnostics now explain this distinction;
`issue_ref_invalid` is still a refusal, not permission to guess and retry.

## Admit your first Issue

The following is a customer-approved **draft-only** JSON checker example. Choose
your own reference, task and exact scope before running it. The sample scope is
the Issue record, manifest and `docs/specs/json-checker` descendants; it does not
reserve paths, authorize foreign edits or implement/approve the application.
Snapshot creation, scope binding and starting progress are separate SDK effects.

This block saves full receipts in a private directory outside the repository.
Python only decodes public read projections; it does not create authority or
import provider internals. Each mutation uses its immediately preceding explicit
read. There is no guard-refresh loop or mutation retry.

```bash
set -eu
: "${AWARE:?Use the absolute command from your installation}"
: "${aware_repo_root:?Set your explicitly initialized absolute repository path}"
if test -n "${CODEX_THREAD_ID-}" && test -z "${CLAUDE_CODE_SESSION_ID-}"; then
  first_issue_actor="codex-$CODEX_THREAD_ID"
elif test -n "${CLAUDE_CODE_SESSION_ID-}" && test -z "${CODEX_THREAD_ID-}"; then
  first_issue_actor="claude_code-$CLAUDE_CODE_SESSION_ID"
else
  echo 'Missing or ambiguous genuine harness identity; remain read-only.' >&2
  exit 2
fi
printf 'Execution: %s\n' "$first_issue_actor"
first_issue_actor_evidence="harness:$first_issue_actor"
first_issue_ref='fb/2026-10-11/json-checker-draft'
first_issue_record='docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md'
first_issue_evidence="$(mktemp -d "${TMPDIR:-/tmp}/aware-first-issue.XXXXXXXX")"
first_issue_intent_prefix="$(basename "$first_issue_evidence")"
printf 'Retain full receipts at %s\n' "$first_issue_evidence"

"$AWARE" issue ensure-snapshot --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --title 'Draft a JSON checker specification' \
  --priority P1 --owner-ref "$first_issue_actor" \
  --source-description 'Customer-approved draft-only example' \
  --problem 'Agents need a shared description of a read-only JSON checker.' \
  --objective 'Create and observe a draft; do not implement or approve it.' \
  --acceptance 'The draft requires that checking never modifies its input.' \
  --client-intent-id "$first_issue_intent_prefix-create" \
  --actor-ref "$first_issue_actor" --actor-evidence-ref "$first_issue_actor_evidence" \
  --format json > "$first_issue_evidence/create.json"

first_issue_read_guard() {
  /usr/bin/python3.12 - "$1" "$first_issue_actor" <<'PY'
import json, re, sys
with open(sys.argv[1], encoding="utf-8") as source:
    result = json.load(source)
if result.get("outcome") != "found":
    raise SystemExit("Issue read did not find the record; retain its full receipt.")
projection = result["projection"]
if projection["identity"]["owner_ref"] != sys.argv[2]:
    raise SystemExit("Issue owner differs from this execution; do not mutate.")
digest = projection["source"]["digest"]
if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
    raise SystemExit("Issue read did not supply an exact source digest.")
print(digest)
PY
}

"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --format json > "$first_issue_evidence/scope-read.json"
first_issue_scope_guard="$(first_issue_read_guard "$first_issue_evidence/scope-read.json")"
"$AWARE" issue bind-scope --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --expected-source-sha256 "$first_issue_scope_guard" \
  --scope-path "$first_issue_record" --scope-path aware.protocol.toml \
  --scope-path docs/specs/json-checker \
  --client-intent-id "$first_issue_intent_prefix-scope" \
  --actor-ref "$first_issue_actor" --actor-evidence-ref "$first_issue_actor_evidence" \
  --format json > "$first_issue_evidence/scope.json"

"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --format json > "$first_issue_evidence/progress-read.json"
first_issue_progress_guard="$(first_issue_read_guard "$first_issue_evidence/progress-read.json")"
"$AWARE" issue start-progress --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --expected-source-sha256 "$first_issue_progress_guard" \
  --client-intent-id "$first_issue_intent_prefix-progress" \
  --actor-ref "$first_issue_actor" --actor-evidence-ref "$first_issue_actor_evidence" \
  --format json > "$first_issue_evidence/progress.json"
"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --format json > "$first_issue_evidence/admitted-read.json"
printf 'Inspect admitted-read.json for owner, in_progress status and exact scope.\n'
```

The final projection should be `outcome=found`, this execution as owner,
`status=in_progress` and exactly the chosen scope. Preserve every receipt.
`harness:<execution>` is declared evidence, not cryptographic authentication.
On nonzero exit stop, retain full stdout/stderr and inspect effects; do not
repeat the block or assume snapshot/scope changes rolled back. This admits work,
not SPEC configuration, draft creation, approval, publication or recovery.

## Prepare a draft for review

After admitting the Issue, use the same installation's
`aware protocol setup-specification` preview/apply to configure the explicit SPEC
binding. Choose customer-approved directories and include every effect in the
Issue's admitted scope. Read the setup receipt before proceeding; preparation
does not configure SPEC or repair a missing binding.

Provide a snapshot input produced through the supported typed authoring
renderer/decoder. Choose its content and definition identity explicitly. This
preparation requires that input to exist: it observes, decodes and renders it
for review, but does not create the snapshot or approve its contents.
No prequalified document package or approved iteration is required. Do not
handwrite approval/authority records or a package-selection JSON.

The attached [typed input example](../workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/examples/prepare_draft_input.py)
prints canonical snapshot bytes through the original public types/encoder. Read
and approve or replace its illustrative JSON-checker terms first. If you choose
to run it, set `aware_envelope_root` to the installer's exact retained directory:

```bash
set -eu
: "${aware_envelope_root:?Set the exact retained_source_and_notices directory}"
: "${aware_init_env:?Use the fresh installation from this guide}"
draft_input_parent="$(mktemp -d)"
draft_snapshot_input="$draft_input_parent/snapshot.json"
test ! -e "$draft_snapshot_input"
test ! -L "$draft_snapshot_input"
"$aware_init_env/bin/python" -I \
  "$aware_envelope_root/source/workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/examples/prepare_draft_input.py" \
  > "$draft_snapshot_input"
```

This only creates an input snapshot in a new private directory outside the
repository. It creates no document, Issue admission, approved gate or iteration.
The gate labels in the example describe intended evidence, not accepted evidence.
Keep the snapshot and review its content before continuing.

Set each variable below to your explicit coordinate or intent before invoking
this complete preparation block. The Issue must already be admitted; author
and intent strings are declared correlation, not authenticated authority.

```bash
set -eu
: "${AWARE:?Use the absolute command from your installation}"
: "${aware_repo_root:?Set your explicitly initialized absolute repository path}"
: "${draft_protocol_manifest:?Set the selected Protocol manifest locator}"
: "${draft_spec_manifest:?Set the intended SPEC manifest locator}"
: "${draft_snapshot_input:?Set the authored snapshot input path}"
: "${first_issue_ref:?Set the existing admitted Issue reference}"
: "${draft_author_ref:?Set the declared draft author}"
: "${draft_authoring_intent_ref:?Set the customer-approved authoring intent}"
: "${draft_client_intent_id:?Set this explicit draft attempt correlation}"
"$AWARE" spec prepare-draft \
  --repository-root "$aware_repo_root" \
  --protocol-manifest "$draft_protocol_manifest" \
  --spec-manifest "$draft_spec_manifest" \
  --snapshot-json "$draft_snapshot_input" \
  --issue-ref "$first_issue_ref" \
  --author-ref "$draft_author_ref" \
  --authoring-intent-ref "$draft_authoring_intent_ref" \
  --client-intent-id "$draft_client_intent_id"
```

Preparation first asks the original Protocol SDK whether the supplied SPEC target
fits the configured binding. It shows the configured root, template, expected
shape, supplied target and owner reason. For an illustrative `docs/specs` binding,
the complete shape is `docs/specs/<spec-key>/aware.spec.toml`: for key
`json-checker`, select `docs/specs/json-checker/aware.spec.toml`, not
`docs/specs/aware.spec.toml`. The owner supplies the actual shape; never assume
this illustrative root overrides your configuration.

A mismatch or typed/uncertain refusal stops with no preview/apply guidance and
no subsequent Issue/input observation. No key is inferred or target corrected.
Select any replacement explicitly, then prepare and review again. A match is
only observed binding layout—not Issue eligibility, destination availability,
semantic approval or guaranteed apply success.

After a validated match, preparation defaults to a readable summary. It labels `issue_source_bytes`,
`protocol_manifest_bytes` and `snapshot_input_bytes`, shows observed Issue
execution/status/scope, and lists the intended document members. It prints
separate original `aware spec create-draft` preview and apply commands with all
three guards. Add `--format json` for original owner observations, rendered
request, member digests and exact argument vectors.

**Review before invocation.** Independent observations are not an atomic
snapshot or an exact publication plan. A validated target-fit match establishes
binding layout only. `status=prepared` does not validate write
authority, Issue execution/lifecycle/scope or destination availability. Those
checks belong to the separately invoked owners. Preparation issues no write
admission, acquires no draft-input custody and never calls preview or apply.

Check the selected repository, manifests, input, Issue execution/status/scope,
author/intent and intended members. Decide whether to invoke the printed preview.
Only after reviewing its outcome decide whether to invoke apply. Printed lines
begin with `aware`; use your installation's absolute `"$AWARE"` in place of that
leading executable and preserve every remaining argument and reviewed guard.
Do not pass the lines to `eval`, execute JSON argument vectors automatically or
recompute guards while copying the command.

```bash
"$AWARE" spec prepare-draft --help
"$AWARE" spec create-draft --help
"$AWARE" spec observe --help
```

The original draft command previews by default; `--apply` is explicit. A
successful apply supplies actual publication, physical/Protocol cleanup and
consumer-completion evidence. A refusal may follow known publication: preserve
all effects, receipts and cleanup/uncertainty evidence; do not assume rollback
or retry the mutation. Observe the published draft through the same installed
`aware spec observe` entrance with explicit repository/manifest coordinates.
Drafting and observation do not approve documents or create approved iterations.

## Guard meanings and path bases

Issue guards identify exact Issue bytes from `projection.source.digest`.
Protocol guards identify exact manifest bytes, not `ProtocolManifest.digest`
(normalized semantic identity). Input guards identify the exact acquired snapshot
bytes, not any resulting SPEC document. All use `sha256:<hex>`; they are not
interchangeable.

Use an absolute repository root and repository-relative Protocol/SPEC manifest
locators for the supported workflow. Keep those locator strings consistent with
the configured binding and the original draft entrance. Snapshot input paths
are absolute or relative to the invoking working directory; preparation retains
the observed absolute source coordinate in the printed command. This does not
make manifest paths relative to that directory or authorize guessed filenames.
Explicit absolute input paths avoid ambiguity.

Apply uses the reviewed guards unchanged. Staleness requires a new preparation
and review decision, never silent guard refresh or automatic retry. Successful
observation of changed bytes does not revive a refused/spent write admission.

## Paired publication and closeout

Before publishing, establish an explicit local Git author separately from init,
observe the current Issue guard and select only admitted exact paths. Inspect:

```bash
"$AWARE" issue commit-workspace --help
"$AWARE" issue publish-close --help
"$AWARE" issue close --help
```

Dry-run the exact publication request before apply. `publish-close` pairs
publication and closeout in one live owner lifetime, but these are two effects,
not an atomic transaction. Preserve both receipts: commits, reference-update
state, index reconciliation, closure refusal, cleanup and known/unknown effects.
A later close refusal does not undo a known commit. A separately invoked
`close` cannot reconstruct the required live publication capability from a
saved Git receipt. Do not republish merely to regain closeout authority or
automatically refresh guards. Retain the original evidence and request an
explicit supported recovery disposition; this guide does not supply a durable
cross-execution closeout migration.

Currentness checks observed state, not every write. Cooperative descriptor
confinement is not continuous confinement. No command silently repairs foreign
work or upgrades filesystem evidence into resident authority.

## Sources and notices

`SOURCE-INDEX.json` binds 1,157 committed selected files to `portable_protocols`
and the exact wheels. It is evidence, not a second selector. Full discovery
inventory remains producer-side. Customer `aware.protocol.toml` configures
record selection/authority, not software packages.

Keep LICENSE, NOTICE, `source/THIRD_PARTY_NOTICES.md`, all source archives,
notices and indexes with the payload. `NOTICE-BINDINGS.json` binds current wheel
identities/resources and openly inventories six missing package-local legal
attachments. Earlier notice indexes and held-input wording stay byte-exact
history, not this envelope's customer authority. Whole-envelope notice acceptance
is recorded for these exact bytes in
[the bounded review status](../releases/canonical-target-fit-fs-v1/REVIEW-STATUS.md);
detached wheels remain unaccepted.

The schema keeps scoped MIT/BSD attribution and adaptations. BSD-3-Clause is
selected while the full upstream file retains its alternative AFL text without
selecting it. Pathspec's MPL terms and corresponding source remain attached.
Packaging's upstream license alternatives and two detected license-index Python
modules are retained; the modules are not additional legal obligations.
Source-derived jsonschema recipe, constraints and publisher source URL/hash
are attached; the original source archive is not.

rpds/pydantic-core component coverage is conservative, not exact binary linkage
or a toolchain attestation. Cython is correlated to msgpack, not PyYAML; LibYAML
is precautionary input from a configurable CI default. `CONTENT-AUDIT.json`
keeps every bounded finding unsuppressed, including relative fixture paths.
This is not exhaustive disclosure clearance or a legal warranty.

Both complete SDK-contract/Meta type-schema libraries are neutral infrastructure,
not Meta/Object or materialization products. Workspace's transitive standalone
`aware-workspace` script is carried, but this candidate does not qualify its
setup/lock workflow or an Agent mount. `aware workspace` remains unavailable;
do not treat script presence as operation admission or bypass the supported
Issue/Protocol/SPEC journey through another launcher.

This installation does not admit Service/API, object execution, materialization,
native receiving or Experience authority. It does not replace aware-dev's
selected contributor command. Instructions are frozen locally, pending independent
review. Public availability and unassisted onboarding are not established by
this instruction freeze.
