# Aware filesystem onboarding

Accepted frozen instructions for the authorized whole-envelope delivery of the
Issue CLI 0.8.3 / FS 0.9.4 composition:
install once, initialize explicitly, admit an Issue and perform governed work.
The whole envelope carries the exact forty-package payload, committed
`portable_protocols` sources and corresponding notices. Exact-envelope technical
and bounded disposition decisions are recorded in the release review status.
See [delivery evidence](../releases/canonical-issue083-fs-v1/PUBLICATION.md) for
the tested public revision and acquisition status.
Scripted installed proofs do not establish unassisted customer onboarding.

## Install with the complete envelope

Qualified target: Linux x86-64 with `/usr/bin/python3.12`. Keep this entire
envelope, including LICENSE, NOTICE, sources, upstream archives and indexes.
Wheel-only acquisition is unsupported: six Code/Workspace wheels still lack
package-local legal attachments. Do not discard the envelope after installation.

From this reviewed checkout root, first read
[distribution terms and source](../releases/canonical-issue083-fs-v1/README.md).
The whole-envelope installer verifies and retains the envelope, then delegates
to its unchanged payload installer. Choose a fresh private environment:

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

## Guarded work and paired publication

Use the same installation's `aware protocol setup-specification` and
`aware spec create-draft` preview/apply, then `aware spec observe`. Inspect
installed help for required typed inputs and explicit coordinates. Draft input
preparation uses the supported typed renderer/decoder, not handmade approval
records or a package-selection JSON. Approved iterations and Goal writers remain
unavailable.

Issue guards identify exact Issue bytes from `projection.source.digest`.
Protocol guards identify exact manifest bytes, not `ProtocolManifest.digest`
(normalized semantic identity). Input guards identify the selected draft input
snapshot. All may use `sha256:<hex>`; their artifacts are not interchangeable.
Manifest/Protocol selection locators are repository-relative. Draft snapshot
paths follow the invoking working directory; explicit absolute input paths
avoid ambiguity. Stale requests refuse: no silent guard refresh or retry.

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

`SOURCE-INDEX.json` binds 1,043 committed selected files to `portable_protocols`
and the exact wheels. It is evidence, not a second selector. Full discovery
inventory remains producer-side. Customer `aware.protocol.toml` configures
record selection/authority, not software packages.

Keep LICENSE, NOTICE, `source/THIRD_PARTY_NOTICES.md`, all source archives,
notices and indexes with the payload. `NOTICE-BINDINGS.json` binds current wheel
identities/resources and openly inventories six missing package-local legal
attachments. Earlier notice indexes and held-input wording stay byte-exact
history, not this envelope's customer authority. Whole-envelope notice acceptance
must be reviewed against these exact bytes; detached wheels remain unaccepted.

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

This installation does not admit Service/API, object execution, materialization,
native receiving or Experience authority. It does not replace aware-dev's
selected contributor command. Public acquisition is recorded separately from
the envelope's technical proof; unassisted onboarding remains unproved.
The [public instruction pins](../releases/canonical-issue083-fs-v1/PUBLIC-INSTRUCTIONS.json)
bind this accepted guidance. Earlier local instruction records remain history,
not current delivery status. Fresh unassisted evaluation follows separately.
